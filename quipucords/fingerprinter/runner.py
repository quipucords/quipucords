"""ScanTask used for network connection discovery."""
import logging
import uuid
from copy import deepcopy
from datetime import datetime

from django.db import DataError
from rest_framework.serializers import DateField

from api.common.common_report import create_report_version
from api.common.util import (
    convert_to_boolean,
    convert_to_float,
    convert_to_int,
    is_boolean,
    is_float,
    is_int,
    mask_data_general,
)
from api.models import DeploymentsReport, Product, ScanTask, SystemFingerprint
from api.serializers import SystemFingerprintSerializer
from constants import DataSources
from fingerprinter import formatters
from fingerprinter.constants import (
    ENTITLEMENTS_KEY,
    META_DATA_KEY,
    NAME_KEY,
    PRESENCE_KEY,
    PRODUCTS_KEY,
    SOURCES_KEY,
)
from fingerprinter.jboss_brms import detect_jboss_brms
from fingerprinter.jboss_eap import detect_jboss_eap
from fingerprinter.jboss_fuse import detect_jboss_fuse
from fingerprinter.jboss_web_server import detect_jboss_ws
from fingerprinter.utils import strip_suffix
from scanner.openshift import formatters as ocp_formatters
from scanner.runner import ScanTaskRunner
from scanner.vcenter.utils import VcenterRawFacts
from utils import deepget, default_getter

logger = logging.getLogger(__name__)

# Keys used to de-duplicate against other network sources
NETWORK_IDENTIFICATION_KEYS = ["subscription_manager_id", "bios_uuid"]

# Keys used to de-duplicate against other VCenter sources
VCENTER_IDENTIFICATION_KEYS = ["vm_uuid"]

# Keys used to de-duplicate against other satellite sources
SATELLITE_IDENTIFICATION_KEYS = ["subscription_manager_id"]

# Keys used to de-duplicate against across sources
NETWORK_SATELLITE_MERGE_KEYS = [
    ("subscription_manager_id", "subscription_manager_id"),
    ("mac_addresses", "mac_addresses"),
]
NETWORK_VCENTER_MERGE_KEYS = [
    ("bios_uuid", "vm_uuid"),
    ("mac_addresses", "mac_addresses"),
]

FINGERPRINT_GLOBAL_ID_KEY = "FINGERPRINT_GLOBAL_ID"

# keys are in reverse order of accuracy (last most accurate)
# (date_key, date_pattern)
RAW_DATE_KEYS = dict(
    [
        ("date_yum_history", ["%Y-%m-%d"]),
        ("date_filesystem_create", ["%Y-%m-%d"]),
        ("date_anaconda_log", ["%Y-%m-%d"]),
        ("registration_time", ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S %z"]),
        ("date_machine_id", ["%Y-%m-%d"]),
        ("creation_timestamp", ["%Y-%m-%dT%H:%M:%S%z"]),
    ]
)

MAC_AND_IP_FACTS = ["ip_addresses", "mac_addresses"]
NAME_RELATED_FACTS = ["name", "vm_dns_name", "virtual_host_name"]

# Fingerprint keys
COMBINED_KEY = "combined_fingerprints"


class FingerprintTaskRunner(ScanTaskRunner):
    """ConnectTaskRunner system connection capabilities.

    Attempts connections to a source using a list of credentials
    and gathers the set of successes (host/ip, credential) and
    failures (host/ip).
    """

    supports_partial_results = False

    @staticmethod
    def format_certs(redhat_certs):
        """Strip the .pem from each cert in the list.

        :param redhat_certs: <list> of redhat certs.
        :returns: <list> of formatted certs.
        """
        try:
            return [int(cert.strip(".pem")) for cert in redhat_certs if cert]
        except Exception:  # noqa: BLE001
            return []

    def execute_task(self, manager_interrupt):
        """Execute fingerprint task."""
        details_report = self.scan_task.details_report

        deployment_report = DeploymentsReport(report_version=create_report_version())
        deployment_report.save()

        # Set the report ids.  Right now they are deployment report id
        # but they do not have to
        deployment_report.report_id = deployment_report.id
        deployment_report.save()

        details_report.deployment_report = deployment_report
        details_report.report_id = deployment_report.id
        details_report.save()

        try:
            message, status = self._process_details_report(
                manager_interrupt, details_report
            )

            self.check_for_interrupt(manager_interrupt)

            if status == ScanTask.COMPLETED:
                deployment_report.status = DeploymentsReport.STATUS_COMPLETE
            else:
                deployment_report.status = DeploymentsReport.STATUS_FAILED
            deployment_report.save()
            return message, status
        except Exception as error:
            # Transition from persisted to failed after engine failed
            deployment_report.status = DeploymentsReport.STATUS_FAILED
            deployment_report.save()
            error_message = (
                f"Fact collection {details_report.id} failed to be processed."
            )

            self.scan_task.log_message(f"{error_message}", log_level=logging.ERROR)
            self.scan_task.log_message(
                f"{error.__class__.__name__}:{error}", log_level=logging.ERROR
            )
            raise error

    def _process_details_report(  # noqa: PLR0915
        self, manager_interrupt, details_report
    ):
        """Process the details report.

        :param manager_interrupt: Signal to indicate job is canceled
        :param details_report: DetailsReport that was saved
        :param scan_task: Task that is running this merge
        :returns: Status message and status
        """
        self.scan_task.log_message("START DEDUPLICATION")

        # Invoke ENGINE to create fingerprints from facts
        fingerprints_list = self._process_sources(details_report)

        self.scan_task.log_message("END DEDUPLICATION")

        number_valid = 0
        number_invalid = 0
        self.scan_task.log_message("START FINGERPRINT PERSISTENCE")
        status_count = 0
        total_count = len(fingerprints_list)
        deployment_report = details_report.deployment_report
        date_field = DateField()
        final_fingerprint_list = []

        valid_fact_attributes = {
            field.name for field in SystemFingerprint._meta.get_fields()
        }

        for fingerprint_dict in fingerprints_list:
            # Remove keys that are not part of SystemFingerprint model
            fingerprint_attributes = set(fingerprint_dict.keys())
            invalid_attributes = fingerprint_attributes - valid_fact_attributes
            for invalid_attribute in invalid_attributes:
                fingerprint_dict.pop(invalid_attribute, None)

            status_count += 1
            name = fingerprint_dict.get("name", "unknown")
            os_release = fingerprint_dict.get("os_release", "unknown")
            self.scan_task.log_message(
                f"FINGERPRINT {status_count} of {total_count} SAVED - Fingerprint "
                f"(name={name}, os_release={os_release})"
            )

            if status_count % 100 == 0:
                self.check_for_interrupt(manager_interrupt)
            fingerprint_dict["deployment_report"] = deployment_report.id
            serializer = SystemFingerprintSerializer(data=fingerprint_dict)
            if serializer.is_valid():
                try:
                    fingerprint = serializer.save()

                    # Add auto-generated fields for the insights report
                    fingerprint_dict["id"] = fingerprint.id

                    # Serialize the date
                    for field in SystemFingerprint.DATE_FIELDS:
                        if fingerprint_dict.get(field, None):
                            fingerprint_dict[field] = date_field.to_representation(
                                fingerprint_dict.get(field)
                            )
                    final_fingerprint_list.append(fingerprint_dict)
                    number_valid += 1
                except DataError as error:
                    number_invalid += 1
                    self.scan_task.log_message(
                        "The fingerprint could not be saved. "
                        f"Fingerprint: {str(error).strip()}. Error: {fingerprint_dict}",
                        log_level=logging.ERROR,
                        exception=error,
                    )
            else:
                number_invalid += 1
                self.scan_task.log_message(
                    f"Invalid fingerprint: {fingerprint_dict}",
                    log_level=logging.ERROR,
                )
                self.scan_task.log_message(
                    f"Fingerprint errors: {serializer.errors}",
                    log_level=logging.ERROR,
                )
            self.scan_task.log_message(
                f"Fingerprints (report id={details_report.id}): {fingerprint_dict}",
                log_level=logging.DEBUG,
            )

        # Mark completed because engine has processed raw facts
        status = ScanTask.COMPLETED
        status_message = "success"
        if final_fingerprint_list:
            deployment_report.status = DeploymentsReport.STATUS_COMPLETE
        else:
            status_message = (
                f"FAILED to create report id={deployment_report.report_id} - "
                "produced no valid fingerprints"
            )
            self.scan_task.log_message(status_message, log_level=logging.ERROR)
            deployment_report.status = DeploymentsReport.STATUS_FAILED
            status = ScanTask.FAILED
        deployment_report.cached_fingerprints = final_fingerprint_list
        deployment_report.cached_masked_fingerprints = mask_data_general(
            deepcopy(final_fingerprint_list), MAC_AND_IP_FACTS, NAME_RELATED_FACTS
        )
        deployment_report.save()
        self.scan_task.log_message(
            f"RESULTS (report id={deployment_report.report_id}) -  "
            f"(valid fingerprints={number_valid}, "
            f"invalid fingerprints={number_invalid})"
        )

        self.scan_task.log_message("END FINGERPRINT PERSISTENCE")
        deployment_report.save()

        return status_message, status

    @staticmethod
    def _format_count_message(fingerprint_map, total_only=False):
        if not total_only:
            message = ", ".join(
                f"{source_type}={len(fingerprints)}"
                for source_type, fingerprints in fingerprint_map.items()
            )
            message += ", "
        else:
            message = ""
        message += f"total={sum(len(fp) for fp in fingerprint_map.values())}"
        return message

    def _log_message_with_count(
        self,
        message,
        fingerprints_per_type,
        log_level=logging.INFO,
        total_only=False,
    ):
        """Log message with fingerprinting count."""
        count_message = self._format_count_message(
            fingerprints_per_type,
            total_only=total_only,
        )
        self.scan_task.log_message(
            f"{message} - Fingerprints ({count_message})",
            log_level=log_level,
        )

    def _process_sources(self, details_report):
        """Process facts and convert to fingerprints.

        :param details_report: DetailsReport containing raw facts
        :returns: list of fingerprints for all systems (all scans)
        """
        # fingerprints per source type
        fingerprint_map = {datasource: [] for datasource in DataSources.values}
        source_list = details_report.sources
        total_source_count = len(source_list)
        self.scan_task.log_message(f"{total_source_count} sources to process")
        source_count = 0
        for source in source_list:
            source_count += 1
            source_type = source.get("source_type")
            source_name = source.get("source_name")
            self.scan_task.log_message(
                f"PROCESSING Source {source_count} of {total_source_count} - "
                f"(name={source_name}, type={source_type},"
                + f" server={source.get('server_id')})"
            )

            source_fingerprints = self._process_source(source)
            fingerprint_map[source_type].extend(source_fingerprints)

            self.scan_task.log_message(
                "SOURCE FINGERPRINTS - "
                f"{len(source_fingerprints)} {source_type} fingerprints"
            )
            self._log_message_with_count("TOTAL FINGERPRINT COUNT", fingerprint_map)

        # Deduplicate network fingerprints
        self.scan_task.log_message(
            "NETWORK DEDUPLICATION by keys %s" % NETWORK_IDENTIFICATION_KEYS
        )
        before_count = len(fingerprint_map[DataSources.NETWORK])
        fingerprint_map[DataSources.NETWORK] = self._remove_duplicate_fingerprints(
            NETWORK_IDENTIFICATION_KEYS,
            fingerprint_map[DataSources.NETWORK],
        )
        self.scan_task.log_message(
            f"NETWORK DEDUPLICATION RESULT - (before={before_count}, "
            f"after={len(fingerprint_map[DataSources.NETWORK])})"
        )

        # Deduplicate satellite fingerprints
        self.scan_task.log_message(
            f"SATELLITE DEDUPLICATION by keys {SATELLITE_IDENTIFICATION_KEYS}"
        )
        before_count = len(fingerprint_map[DataSources.SATELLITE])
        fingerprint_map[DataSources.SATELLITE] = self._remove_duplicate_fingerprints(
            SATELLITE_IDENTIFICATION_KEYS, fingerprint_map[DataSources.SATELLITE]
        )
        self.scan_task.log_message(
            f"SATELLITE DEDUPLICATION RESULT - (before={before_count}, "
            f"after={len(fingerprint_map[DataSources.SATELLITE])})"
        )

        # Deduplicate vcenter fingerprints
        self.scan_task.log_message(
            f"VCENTER DEDUPLICATION by keys {VCENTER_IDENTIFICATION_KEYS}"
        )
        before_count = len(fingerprint_map[DataSources.VCENTER])
        fingerprint_map[DataSources.VCENTER] = self._remove_duplicate_fingerprints(
            VCENTER_IDENTIFICATION_KEYS, fingerprint_map[DataSources.VCENTER]
        )
        self.scan_task.log_message(
            f"VCENTER DEDUPLICATION RESULT - (before={before_count}, "
            f"after={len(fingerprint_map[DataSources.VCENTER])})"
        )

        self._log_message_with_count("TOTAL FINGERPRINT COUNT", fingerprint_map)

        # Merge network and satellite fingerprints
        self.scan_task.log_message(
            "NETWORK and SATELLITE DEDUPLICATION "
            "by keys pairs [(network_key, satellite_key)]=%s"
            % NETWORK_SATELLITE_MERGE_KEYS
        )

        self._log_message_with_count(
            "NETWORK and SATELLITE DEDUPLICATION START COUNT", fingerprint_map
        )

        _, fingerprint_map[COMBINED_KEY] = self._merge_fingerprints_from_source_types(
            NETWORK_SATELLITE_MERGE_KEYS,
            fingerprint_map[DataSources.NETWORK],
            fingerprint_map[DataSources.SATELLITE],
        )
        # remove keys already combined
        fingerprint_map.pop(DataSources.NETWORK)
        fingerprint_map.pop(DataSources.SATELLITE)
        self._log_message_with_count(
            "NETWORK and SATELLITE DEDUPLICATION END COUNT", fingerprint_map
        )

        # Merge network and vcenter fingerprints
        reverse_priority_keys = ("cpu_count", "infrastructure_type")
        self.scan_task.log_message(
            "NETWORK-SATELLITE and VCENTER DEDUPLICATION"
            " by keys pairs "
            "[(network_satellite_key, vcenter_key)]=%s" % NETWORK_VCENTER_MERGE_KEYS
        )
        self.scan_task.log_message(
            "NETWORK-SATELLITE and VCENTER DEDUPLICATION"
            " by reverse priority keys "
            f"(we trust vcenter more than network/satellite): {reverse_priority_keys}"
        )

        self._log_message_with_count(
            "NETWORK-SATELLITE and VCENTER DEDUPLICATION START COUNT",
            fingerprint_map,
        )

        _, fingerprint_map[COMBINED_KEY] = self._merge_fingerprints_from_source_types(
            NETWORK_VCENTER_MERGE_KEYS,
            fingerprint_map[COMBINED_KEY],
            fingerprint_map[DataSources.VCENTER],
            reverse_priority_keys=reverse_priority_keys,
        )
        # remove already combined key
        fingerprint_map.pop(DataSources.VCENTER)
        self._log_message_with_count(
            "NETWORK-SATELLITE and VCENTER DEDUPLICATION END COUNT",
            fingerprint_map,
        )

        # openshift/ansible fingerprints - These won't be deduplicated or merged
        fingerprint_map[COMBINED_KEY].extend(fingerprint_map.pop(DataSources.OPENSHIFT))
        fingerprint_map[COMBINED_KEY].extend(fingerprint_map.pop(DataSources.ANSIBLE))
        self._log_message_with_count(
            "COMBINE with OPENSHIFT+ANSIBLE fingerprints",
            fingerprint_map,
            total_only=True,
        )

        self._post_process_merged_fingerprints(fingerprint_map[COMBINED_KEY])
        return fingerprint_map[COMBINED_KEY]

    def _post_process_merged_fingerprints(self, fingerprints):
        """Normalize cross source fingerprint values.

        This is required when values need cross source complex
        logic.
        :param fingerprints: final list of fingerprints
        associated with facts.
        """
        self.scan_task.log_message(
            "POST MERGE PROCESSING BEGIN - computing system creation time"
        )
        for fingerprint in fingerprints:
            fingerprint[SOURCES_KEY] = list(fingerprint[SOURCES_KEY].values())
            self._compute_system_creation_time(fingerprint)
        self.scan_task.log_message(
            "POST MERGE PROCESSING END - computing system creation time"
        )

    def _compute_system_creation_time(self, fingerprint):
        """Normalize cross source fingerprint values.

        This is required when values need cross source complex
        logic.
        :param fingerprints: final list of fingerprints
        associated with facts.
        """
        # keys are in reverse order of accuracy (last most accurate)
        system_creation_date = None
        system_creation_date_metadata = {}
        sys_creation_key = "system_creation_date"
        for date_key, date_pattern in RAW_DATE_KEYS.items():
            date_value = fingerprint.pop(date_key, None)
            date_metadata_dict = fingerprint[META_DATA_KEY].pop(date_key, None)
            if date_value is not None:
                system_creation_date_metadata = date_metadata_dict
                system_creation_date = self._multi_format_dateparse(
                    system_creation_date_metadata, date_key, date_value, date_pattern
                )

        if not system_creation_date_metadata:
            # no fact for system_creation_date detected (openshift scan?). skipping...
            return

        fingerprint[sys_creation_key] = system_creation_date
        if system_creation_date is not None:
            fingerprint[META_DATA_KEY][sys_creation_key] = system_creation_date_metadata
        else:
            raw_fact_key = "/".join(RAW_DATE_KEYS.keys())
            system_creation_date_metadata["raw_fact_key"] = raw_fact_key
            fingerprint[META_DATA_KEY][sys_creation_key] = system_creation_date_metadata

    def process_facts_for_datasource(
        self, data_source: DataSources, source: dict, fact_dict: dict
    ) -> dict:
        """Process facts for a given DataSource.

        :param data_source: DataSources enum
        :param fact_dict: dict of facts to process
        :returns: dict of fingerprints detected in fact_dict
        """
        try:
            process_fn = getattr(self, f"_process_{data_source}_fact")
        except AttributeError as err:
            raise NotImplementedError(
                f"No method implemented for '{data_source}'."
            ) from err
        return process_fn(source, fact_dict)

    def _process_source(self, source):
        """Process facts and convert to fingerprints.

        :param source: The JSON source information
        :returns: fingerprints produced from facts
        """
        fingerprints = []
        for fact in source["facts"]:
            fingerprint = None
            server_id = source.get("server_id")
            source_type = source.get("source_type")
            source_name = source.get("source_name")
            if fact.get("cluster") and source_type == DataSources.OPENSHIFT:
                # skip cluster fact in openshift scans since this type of "system"
                # won't generate a fingerprint
                continue

            try:
                fingerprint = self.process_facts_for_datasource(
                    source_type, source, fact
                )
            except KeyError:
                self.scan_task.log_message.error(
                    "Could not process source, " f"unknown source type: {source_type}",
                    log_level=logging.ERROR,
                )

            if fingerprint is not None:
                fingerprint[SOURCES_KEY] = {
                    f"{server_id}+{source_name}": {
                        "server_id": server_id,
                        "source_type": source_type,
                        "source_name": source_name,
                    }
                }
                fingerprints.append(fingerprint)

        return fingerprints

    def _merge_fingerprints_from_source_types(
        self, merge_keys_list, base_list, merge_list, reverse_priority_keys=None
    ):
        """Merge fingerprints from multiple sources.

        :param base_list: base list
        :param merge_list: fact to process
        :returns: int indicating number merged and
        list of all fingerprints wihtout duplicates
        :param reverse_priority_keys: Set of keys in to_merge_fingerprint
        that should reverse the priority.  In other words, the value
        of to_merge_fingerprint should be used instead of the
        priority_fingerprint value.
        """
        number_merged = 0

        # Check to make sure a merge is required at all
        if not merge_list:
            return number_merged, base_list

        if not base_list:
            return number_merged, merge_list

        # start with the base_list fingerprints
        result = base_list[:]
        to_merge = merge_list[:]
        for key_tuple in merge_keys_list:
            key_merged_count, result, to_merge = self._merge_matching_fingerprints(
                key_tuple[0],
                result,
                key_tuple[1],
                to_merge,
                reverse_priority_keys=reverse_priority_keys,
            )
            number_merged += key_merged_count

        # Add remaining as they didn't match anything (no merge)
        result = result + to_merge
        return number_merged, result

    def _merge_matching_fingerprints(  # noqa: PLR0913
        self,
        base_key,
        base_list,
        candidate_key,
        candidate_list,
        reverse_priority_keys=None,
    ):
        """Given keys and two lists, merge on key equality.

        Given two lists of fingerprints, match on provided keys and merge
        if keys match.  Base values have precedence.
        :param base_key: base_key used to create an index of base_list
        :param base_list: list of dict objects
        :param candidate_key: candidate_key used to create an index of
        candidate_list
        :param candidate_list: list of dict objects
        :returns: int indicating number merged and
        fingerprint produced from fact
        :param reverse_priority_keys: Set of keys in to_merge_fingerprint
        that should reverse the priority.  In other words, the value
        of to_merge_fingerprint should be used instead of the
        priority_fingerprint value.
        """
        base_dict, base_no_key = self._create_index_for_fingerprints(
            base_key, base_list
        )
        candidate_dict, candidate_no_key = self._create_index_for_fingerprints(
            candidate_key, candidate_list
        )

        # Initialize lists with values that cannot be compared
        base_match_list = []
        candidate_no_match_list = []

        number_merged = 0
        # Match candidate to base fingerprint using index key
        for candidate_index_key, candidate_fingerprint in candidate_dict.items():
            # For each overlay fingerprint check for matching base fingerprint
            # using candidate_index_key.  Remove so value is not in
            # left-over set
            base_value = base_dict.pop(candidate_index_key, None)
            if base_value:
                # candidate_index_key == base_key so merge
                merged_value = self._merge_fingerprint(
                    base_value,
                    candidate_fingerprint,
                    reverse_priority_keys=reverse_priority_keys,
                )
                number_merged += 1

                # Add merged value to key
                base_match_list.append(merged_value)
            else:
                # Could not merge, so add to not merged list
                candidate_no_match_list.append(candidate_fingerprint)

        # Merge base items without key, matched, and remainder
        # who did not match
        base_result_list = base_no_key + base_match_list + list(base_dict.values())
        base_result_list = self._remove_duplicate_fingerprints(
            [FINGERPRINT_GLOBAL_ID_KEY], base_result_list, True
        )

        # Merge candidate items without key list with those that didn't match
        candidate_no_match_list = candidate_no_key + candidate_no_match_list
        candidate_no_match_list = self._remove_duplicate_fingerprints(
            [FINGERPRINT_GLOBAL_ID_KEY], candidate_no_match_list, True
        )

        return number_merged, base_result_list, candidate_no_match_list

    def _remove_duplicate_fingerprints(
        self, id_key_list, fingerprint_list, remove_key=False
    ):
        """Given a list of dict remove duplicates.

        Takes fingerprint_list and retrieves dict value for
        FINGERPRINT_GLOBAL_ID_KEY. Builds a map using this.  A
        fingerprint that was duplicated for mac_address comparision will
        have the samme FINGERPRINT_GLOBAL_ID_KEY.
        :param id_key_list: keys used to evaulate uniqueness
        :param fingerprint_list: list of dict objects to be keyed by id_key
        :param remove_key: bool that determines if the id_key and its value
        should be removed from fingerprint
        :returns: list of fingerprints that is unique
        """
        if not fingerprint_list:
            return fingerprint_list

        result_list = deepcopy(fingerprint_list)
        for id_key in id_key_list:
            unique_dict = {}
            no_global_id_list = []
            for fingerprint in result_list:
                unique_id_value = fingerprint.get(id_key)
                if unique_id_value:
                    # Add or update fingerprint value
                    existing_fingerprint = unique_dict.get(unique_id_value)
                    if existing_fingerprint:
                        unique_dict[unique_id_value] = self._merge_fingerprint(
                            existing_fingerprint, fingerprint
                        )
                    else:
                        unique_dict[unique_id_value] = fingerprint
                else:
                    no_global_id_list.append(fingerprint)

            result_list = no_global_id_list + list(unique_dict.values())

            # Strip id key from fingerprints if requested
            if remove_key:
                for fingerprint in result_list:
                    fingerprint.pop(id_key, None)

        return result_list

    def _create_index_for_fingerprints(
        self, id_key, fingerprint_list, create_global_id=True
    ):
        """Given a list of dict, create index by id_key.

        Takes fingerprint_list and retrieves dict value for id_key.
        Adds this to a result dict by id_key values.  For example,
        given a list of system fact dict, creates a dict of systems
        by mac_address.
        :param id_key: key to use in dict creation
        :param fingerprint_list: list of dict objects to be keyed by id_key
        :param create_global_id: If True, a new key/value is placed in the
        index.  The key is FINGERPRINT_GLOBAL_ID_KEY and the value is a newly
        generated UUID.  This allows you to de-duplicate later if needed.
        :returns: dict of values keyed by id_key and list of values
        who do not have the id_key
        """
        result_by_key = {}
        key_not_found_list = []
        number_duplicates = 0
        fingerprint_list = deepcopy(fingerprint_list)
        for value_dict in fingerprint_list:
            # Add globally unique key for de-duplication later
            if create_global_id:
                value_dict[FINGERPRINT_GLOBAL_ID_KEY] = str(uuid.uuid4())
            id_key_value = value_dict.get(id_key)
            if id_key_value:
                if isinstance(id_key_value, list):
                    # value is list so explode
                    for list_value in id_key_value:
                        if result_by_key.get(list_value) is None:
                            result_by_key[list_value] = value_dict
                        else:
                            number_duplicates += 1
                else:
                    if result_by_key.get(id_key_value) is None:  # noqa: PLR5501
                        result_by_key[id_key_value] = value_dict
                    else:
                        number_duplicates += 1
            else:
                key_not_found_list.append(value_dict)
        if number_duplicates:
            self.scan_task.log_message(
                "_create_index_for_fingerprints - "
                "Potential lost fingerprint due to duplicate"
                + f" {id_key}: {number_duplicates}.",
                log_level=logging.DEBUG,
            )
        return result_by_key, key_not_found_list

    def _merge_fingerprint(  # noqa: PLR0912, C901
        self,
        priority_fingerprint: dict,
        to_merge_fingerprint: dict,
        reverse_priority_keys=None,
    ) -> dict:
        """Merge two fingerprints.

        The priority_fingerprint values are always used.  The
        to_merge_fingerprint values are only used when the priority_fingerprint
        is missing the same values.
        :param priority_fingerprint: Fingerprint that has precedence if
        both have the same attribute.
        :param to_merge_fingerprint: Fingerprint whose values are used
        when attributes are not in priority_fingerprint
        :param reverse_priority_keys: Set of keys in to_merge_fingerprint
        that should reverse the priority.  In other words, the value
        of to_merge_fingerprint should be used instead of the
        priority_fingerprint value.
        """
        priority_fingerprint = deepcopy(priority_fingerprint)
        to_merge_fingerprint = deepcopy(to_merge_fingerprint)
        priority_keys = set(priority_fingerprint.keys())
        to_merge_keys = set(to_merge_fingerprint.keys())

        # Merge keys from to_merge into priority.  These
        # are keys not in priority or have a reverse priority.
        keys_to_add_list = to_merge_keys - priority_keys

        # Additionally, add reverse priority keys
        if reverse_priority_keys is not None and isinstance(reverse_priority_keys, set):
            keys_to_add_list = keys_to_add_list | reverse_priority_keys

        non_fact_keys = set([ENTITLEMENTS_KEY, META_DATA_KEY, PRODUCTS_KEY])
        for key in (priority_keys & to_merge_keys) - non_fact_keys:
            if (
                priority_fingerprint[key] is None
                and to_merge_fingerprint[key] is not None
            ):
                # reverse the priority since value is None
                keys_to_add_list.add(key)
                continue

            # If priority do not have sudo and to merge has sudo
            # use the to merge value
            priority_sudo = (
                priority_fingerprint.get(META_DATA_KEY, {})
                .get(key, {})
                .get("has_sudo", False)
            )
            to_merge_sudo = (
                to_merge_fingerprint.get(META_DATA_KEY, {})
                .get(key, {})
                .get("has_sudo", False)
            )
            if not priority_sudo and to_merge_sudo:
                keys_to_add_list.add(key)

        # merge facts
        for fact_key in keys_to_add_list:
            to_merge_fact = to_merge_fingerprint.get(fact_key)
            priority_fingerprint[META_DATA_KEY][fact_key] = to_merge_fingerprint[
                META_DATA_KEY
            ][fact_key]
            priority_fingerprint[fact_key] = to_merge_fact

        # merge sources
        priority_sources = priority_fingerprint[SOURCES_KEY]
        to_merge_sources = to_merge_fingerprint[SOURCES_KEY]

        for source in to_merge_sources:
            if source not in priority_sources.keys():
                priority_sources[source] = to_merge_sources[source]

        # merge entitlements
        if to_merge_fingerprint.get(ENTITLEMENTS_KEY):
            combined_entitlements_list = priority_fingerprint.get(
                ENTITLEMENTS_KEY, []
            ) + to_merge_fingerprint.get(ENTITLEMENTS_KEY, [])

            unique_entitlement_dict = {}
            unique_entitlement_list = []
            # remove duplicate entitlements
            for entitlement in combined_entitlements_list:
                # entitlements have a name, entitlement_id or both
                unique_entitlement_id = (
                    f"{entitlement.get('name', '_')}:"
                    + f"{entitlement.get('entitlement_id', '_')}"
                )
                if unique_entitlement_dict.get(unique_entitlement_id) is None:
                    # we haven't seen this entitlement
                    unique_entitlement_dict[unique_entitlement_id] = entitlement
                    unique_entitlement_list.append(entitlement)

            priority_fingerprint[ENTITLEMENTS_KEY] = unique_entitlement_list

        # merge products
        if to_merge_fingerprint.get(PRODUCTS_KEY):
            if PRODUCTS_KEY not in priority_fingerprint:
                priority_fingerprint[PRODUCTS_KEY] = to_merge_fingerprint.get(
                    PRODUCTS_KEY, []
                )
            else:
                priority_prod_dict = {}
                priority_prod = priority_fingerprint.get(PRODUCTS_KEY, [])
                to_merge_prod = to_merge_fingerprint.get(PRODUCTS_KEY, [])
                for prod in priority_prod:
                    priority_prod_dict[prod[NAME_KEY]] = prod
                for prod in to_merge_prod:
                    merge_prod = priority_prod_dict.get(prod[NAME_KEY])
                    presence = merge_prod.get(PRESENCE_KEY)
                    if (
                        merge_prod
                        and presence == Product.ABSENT
                        and prod.get(PRESENCE_KEY) != Product.ABSENT
                    ):
                        priority_prod_dict[prod[NAME_KEY]] = prod
                    elif merge_prod is None:
                        priority_prod_dict[prod[NAME_KEY]] = prod
                priority_fingerprint[PRODUCTS_KEY] = list(priority_prod_dict.values())

        return priority_fingerprint

    def _add_fact_to_fingerprint(  # noqa: PLR0913
        self,
        source: dict,
        raw_fact_key: str,
        raw_fact: dict,
        fingerprint_key: str,
        fingerprint: dict,
        fact_value=None,
        fact_formatter=None,
    ):
        """Create the fingerprint fact and metadata.

        :param source: Source used to gather raw facts.
        :param raw_fact_key: Raw fact key used to obtain value
        :param raw_fact: Raw fact used to obtain value
        :param fingerprint_key: Key used to store fingerprint
        :param fingerprint: dict containing all fingerprint facts
        this fact.
        :param fact_value: Used when values are computed from
        raw facts instead of direct access.
        :param fact_formatter: A function that will format the fact - it should expect
        the raw fact in its signature.
        """
        actual_fact_value = None
        raw_fact_value = deepget(raw_fact, raw_fact_key)
        if fact_value is not None and fact_formatter is not None:
            raise AssertionError(
                "fact_value and fact_formatter can't be used together."
            )
        if fact_value is not None:
            actual_fact_value = fact_value
        elif fact_formatter is not None:
            actual_fact_value = fact_formatter(raw_fact_value)
        elif raw_fact_value is not None:
            actual_fact_value = raw_fact_value

        # Remove empty string values
        if isinstance(actual_fact_value, str) and not actual_fact_value:
            actual_fact_value = None
        if is_boolean(actual_fact_value):
            actual_fact_value = convert_to_boolean(actual_fact_value)
        elif is_float(actual_fact_value):
            actual_fact_value = convert_to_float(actual_fact_value)
        elif is_int(actual_fact_value):
            actual_fact_value = convert_to_int(actual_fact_value)

        fingerprint[fingerprint_key] = actual_fact_value
        fingerprint[META_DATA_KEY][fingerprint_key] = {
            "server_id": source["server_id"],
            "source_name": source["source_name"],
            "source_type": source["source_type"],
            "raw_fact_key": raw_fact_key,
            "has_sudo": raw_fact.get("user_has_sudo", False),
        }

    def _add_products_to_fingerprint(self, source, raw_fact, fingerprint):
        """Create the fingerprint products with fact and metadata.

        :param source: Source used to gather raw facts.
        :param raw_fact: Raw fact used to obtain value
        :param fingerprint: dict containing all fingerprint facts
        this fact.
        """
        eap = detect_jboss_eap(source, raw_fact)
        fuse = detect_jboss_fuse(source, raw_fact)
        brms = detect_jboss_brms(source, raw_fact)
        jws = detect_jboss_ws(source, raw_fact)
        fingerprint["products"] = [eap, fuse, brms, jws]

    def _add_entitlements_to_fingerprint(
        self, source, raw_fact_key, raw_fact, fingerprint
    ):
        """Create the fingerprint entitlements with fact and metadata.

        :param source: Source used to gather raw facts.
        :param raw_fact_key: Raw fact key used to obtain value
        :param raw_fact: Raw fact used to obtain value
        :param fingerprint: dict containing all fingerprint facts
        this fact.
        """
        actual_fact_value = None
        if raw_fact.get(raw_fact_key) is not None:
            actual_fact_value = raw_fact.get(raw_fact_key)
        entitlements = []
        if actual_fact_value is not None and isinstance(actual_fact_value, list):
            for entitlement in actual_fact_value:
                add = False
                f_ent = {}
                if entitlement.get("name"):
                    f_ent["name"] = entitlement.get("name")
                    add = True
                if entitlement.get("entitlement_id"):
                    f_ent["entitlement_id"] = entitlement.get("entitlement_id")
                    add = True
                if add:
                    f_ent[META_DATA_KEY] = {
                        "server_id": source["server_id"],
                        "source_name": source["source_name"],
                        "source_type": source["source_type"],
                        "raw_fact_key": raw_fact_key,
                    }
                    entitlements.append(f_ent)

            fingerprint[ENTITLEMENTS_KEY] = entitlements
        else:
            fingerprint[ENTITLEMENTS_KEY] = entitlements

    def _process_network_fact(self, source: dict, fact: dict) -> dict:
        """Process a fact and convert to a fingerprint.

        :param source: The source that provided this fact.
        :param facts: fact to process
        :returns: fingerprint produced from fact
        """
        fingerprint = {META_DATA_KEY: {}}

        # Use a list to drive direct mappings of raw_fact_key, fingerprint_key pairs.
        raw_fact_keys_to_fingerprint_keys = [
            # Common facts
            ("uname_hostname", "name"),
            ("uname_processor", "architecture"),
            # Red Hat facts
            ("redhat_packages_gpg_num_rh_packages", "redhat_package_count"),
            ("redhat_packages_certs", "redhat_certs"),
            ("redhat_packages_gpg_is_redhat", "is_redhat"),
            ("etc_machine_id", "etc_machine_id"),
            # Set OS information
            ("etc_release_name", "os_name"),
            ("etc_release_version", "os_version"),
            ("etc_release_release", "os_release"),
            # Get IPv4 addresses from ifconfig's fact if present, else from ip's fact.
            (
                "ifconfig_ip_addresses"
                if deepget(fact, "ifconfig_ip_addresses") is not None
                else "ip_address_show_ipv4",
                "ip_addresses",
            ),
            # Set CPU facts
            ("cpu_count", "cpu_count"),
            # Network scan specific facts
            ("dmi_system_uuid", "bios_uuid"),
            ("subscription_manager_id", "subscription_manager_id"),
            # System information
            ("cpu_socket_count", "cpu_socket_count"),
            ("cpu_core_count", "cpu_core_count"),
            ("cpu_core_per_socket", "cpu_core_per_socket"),
            ("cpu_hyperthreading", "cpu_hyperthreading"),
            # Determine system_creation_date
            ("date_machine_id", "date_machine_id"),
            ("date_anaconda_log", "date_anaconda_log"),
            ("date_filesystem_create", "date_filesystem_create"),
            ("date_yum_history", "date_yum_history"),
            ("insights_client_id", "insights_client_id"),
            # public cloud fact
            ("cloud_provider", "cloud_provider"),
            # user data facts
            ("system_user_count", "system_user_count"),
            ("user_login_history", "user_login_history"),
            # System purpose facts
            ("system_purpose_json", "system_purpose"),
            ("system_purpose_json__role", "system_role"),
            ("system_purpose_json__addons", "system_addons"),
            (
                "system_purpose_json__service_level_agreement",
                "system_service_level_agreement",
            ),
            ("system_purpose_json__usage", "system_usage_type"),
            # Determine if VM facts
            ("virt_type", "virtualized_type"),
            ("system_memory_bytes", "system_memory_bytes"),
        ]

        for raw_fact_key, fingerprint_key in raw_fact_keys_to_fingerprint_keys:
            self._add_fact_to_fingerprint(
                source, raw_fact_key, fact, fingerprint_key, fingerprint
            )

        # Get MAC addresses from ifconfig's fact if present, else from ip's fact.
        mac_addresses_raw_fact_key = (
            "ifconfig_mac_addresses"
            if deepget(fact, "ifconfig_mac_addresses") is not None
            else "ip_address_show_mac"
        )
        self._add_fact_to_fingerprint(
            source,
            mac_addresses_raw_fact_key,
            fact,
            "mac_addresses",
            fingerprint,
            fact_formatter=formatters.format_mac_addresses,
        )

        last_checkin = None
        if fact.get("connection_timestamp"):
            last_checkin = self._multi_format_dateparse(
                source,
                "connection_timestamp",
                fact["connection_timestamp"],
                ["%Y%m%d%H%M%S"],
            )
        self._add_fact_to_fingerprint(
            source,
            "connection_timestamp",
            fact,
            "system_last_checkin_date",
            fingerprint,
            fact_value=last_checkin,
        )

        # Determine if running on VM or bare metal
        virt_what_type = fact.get("virt_what_type")
        if virt_what_type == "bare metal":
            raw_fact_key = "virt_what_type"
            fact_value = SystemFingerprint.BARE_METAL
        elif fact.get("virt_type"):
            raw_fact_key = "virt_type"
            fact_value = SystemFingerprint.VIRTUALIZED
        elif fact.get("subman_virt_is_guest", False):
            # We don't know virt_type, but subscription-manager says it's a guest.
            # So, we assume it's virtualized. See also: DISCOVERY-243.
            raw_fact_key = "subman_virt_is_guest"
            fact_value = SystemFingerprint.VIRTUALIZED
        elif virt_what_type:
            # virt_what_type is not "bare metal" or None, but we have no other details.
            raw_fact_key = "virt_what_type"
            fact_value = SystemFingerprint.UNKNOWN
        else:
            raw_fact_key = "virt_what_type/virt_type"
            fact_value = SystemFingerprint.UNKNOWN
        self._add_fact_to_fingerprint(
            source,
            raw_fact_key,
            fact,
            "infrastructure_type",
            fingerprint,
            fact_value=fact_value,
        )

        self._add_entitlements_to_fingerprint(
            source, "subman_consumed", fact, fingerprint
        )
        self._add_products_to_fingerprint(source, fact, fingerprint)

        return fingerprint

    def _process_vcenter_fact(self, source, fact):
        """Process a fact and convert to a fingerprint.

        :param source: The source that provided this fact.
        :param facts: fact to process
        :returns: fingerprint produced from fact
        """
        fingerprint = {META_DATA_KEY: {}}

        # Common facts
        # Set name
        if fact.get("vm.dns_name"):
            raw_fact_key = "vm.dns_name"
        else:
            raw_fact_key = "vm.name"

        self._add_fact_to_fingerprint(source, raw_fact_key, fact, "name", fingerprint)

        self._add_fact_to_fingerprint(source, "vm.os", fact, "os_release", fingerprint)
        self._add_fact_to_fingerprint(
            source,
            "vm.os",
            fact,
            "is_redhat",
            fingerprint,
            fact_formatter=formatters.is_redhat_from_vm_os,
        )
        self._add_fact_to_fingerprint(
            source,
            "vcenter_source",
            fact,
            "infrastructure_type",
            fingerprint,
            fact_value="virtualized",
        )
        self._add_fact_to_fingerprint(
            source,
            "vm.mac_addresses",
            fact,
            "mac_addresses",
            fingerprint,
            fact_formatter=formatters.format_mac_addresses,
        )
        self._add_fact_to_fingerprint(
            source, "vm.ip_addresses", fact, "ip_addresses", fingerprint
        )
        self._add_fact_to_fingerprint(
            source, "vm.cpu_count", fact, "cpu_count", fingerprint
        )
        self._add_fact_to_fingerprint(
            source, "uname_processor", fact, "architecture", fingerprint
        )

        # VCenter specific facts
        self._add_fact_to_fingerprint(source, "vm.state", fact, "vm_state", fingerprint)
        self._add_fact_to_fingerprint(source, "vm.uuid", fact, "vm_uuid", fingerprint)

        last_checkin = None
        if fact.get("vm.last_check_in"):
            last_checkin = self._multi_format_dateparse(
                source,
                "vm.last_check_in",
                fact["vm.last_check_in"],
                ["%Y-%m-%d %H:%M:%S"],
            )
        self._add_fact_to_fingerprint(
            source,
            "vm.last_check_in",
            fact,
            "system_last_checkin_date",
            fingerprint,
            fact_value=last_checkin,
        )

        self._add_fact_to_fingerprint(
            source, "vm.dns_name", fact, "vm_dns_name", fingerprint
        )
        self._add_fact_to_fingerprint(
            source, "vm.host.name", fact, "virtual_host_name", fingerprint
        )
        self._add_fact_to_fingerprint(
            source, "vm.host.uuid", fact, "virtual_host_uuid", fingerprint
        )
        self._add_fact_to_fingerprint(
            source, "vm.host.cpu_count", fact, "vm_host_socket_count", fingerprint
        )
        self._add_fact_to_fingerprint(
            source, "vm.host.cpu_cores", fact, "vm_host_core_count", fingerprint
        )
        self._add_fact_to_fingerprint(
            source, "vm.datacenter", fact, "vm_datacenter", fingerprint
        )
        self._add_fact_to_fingerprint(
            source, "vm.cluster", fact, "vm_cluster", fingerprint
        )

        # VcenterRawFacts.MEMORY_SIZE is formatted in GB. lets convert it to mb
        # https://github.com/quipucords/quipucords/blob/bf1f034b6596ba01c9c89f766088108dd3f421fc/quipucords/scanner/vcenter/inspect.py#L190-L191
        self._add_fact_to_fingerprint(
            source,
            VcenterRawFacts.MEMORY_SIZE,
            fact,
            "system_memory_bytes",
            fingerprint,
            fact_formatter=formatters.gigabytes_to_bytes,
        )

        fingerprint[ENTITLEMENTS_KEY] = []
        fingerprint[PRODUCTS_KEY] = []

        return fingerprint

    def _process_satellite_fact(self, source, fact):  # noqa: PLR0915
        """Process a fact and convert to a fingerprint.

        :param source: The source that provided this fact.
        :param facts: fact to process
        :returns: fingerprint produced from fact
        """
        rhel_versions = {
            "4Server": "Red Hat Enterprise Linux 4 Server",
            "5Server": "Red Hat Enterprise Linux 5 Server",
            "6Server": "Red Hat Enterprise Linux 6 Server",
            "7Server": "Red Hat Enterprise Linux 7 Server",
            "8Server": "Red Hat Enterprise Linux 8 Server",
        }

        fingerprint = {META_DATA_KEY: {}}

        # Common facts
        self._add_fact_to_fingerprint(source, "hostname", fact, "name", fingerprint)

        self._add_fact_to_fingerprint(source, "os_name", fact, "os_name", fingerprint)
        # Get the os name
        satellite_os_name = default_getter(fact, "os_name", "")
        is_redhat = False
        rhel_version = None
        # if the os name is none
        if not satellite_os_name:
            # grab the os release
            satellite_os_release = fact.get("os_release", "")
            if satellite_os_release in rhel_versions:
                # if the os release is a rhel version
                # 1. set the is redhat fact to true and add it to fingerprint
                # 2. set the rhel version to the rhel versions value
                is_redhat = True
                rhel_version = rhel_versions[satellite_os_release]
            self._add_fact_to_fingerprint(
                source,
                "os_release",
                fact,
                "is_redhat",
                fingerprint,
                fact_value=is_redhat,
            )
        else:
            # if the os name indicates redhat, set is_redhat to true
            rhel_os_names = ["rhel", "redhat", "redhatenterpriselinux"]
            if satellite_os_name.lower().replace(" ", "") in rhel_os_names:
                is_redhat = True
            self._add_fact_to_fingerprint(
                source, "os_name", fact, "is_redhat", fingerprint, fact_value=is_redhat
            )
        if rhel_version:
            self._add_fact_to_fingerprint(
                source,
                "os_release",
                fact,
                "os_release",
                fingerprint,
                fact_value=rhel_version,
            )
        else:
            self._add_fact_to_fingerprint(
                source, "os_release", fact, "os_release", fingerprint
            )

        self._add_fact_to_fingerprint(
            source, "os_version", fact, "os_version", fingerprint
        )

        self._add_fact_to_fingerprint(
            source,
            "mac_addresses",
            fact,
            "mac_addresses",
            fingerprint,
            fact_formatter=formatters.format_mac_addresses,
        )
        self._add_fact_to_fingerprint(
            source, "ip_addresses", fact, "ip_addresses", fingerprint
        )

        self._add_fact_to_fingerprint(source, "cores", fact, "cpu_count", fingerprint)
        self._add_fact_to_fingerprint(
            source, "architecture", fact, "architecture", fingerprint
        )

        # Common network/satellite
        self._add_fact_to_fingerprint(
            source, "uuid", fact, "subscription_manager_id", fingerprint
        )
        self._add_fact_to_fingerprint(
            source, "virt_type", fact, "virtualized_type", fingerprint
        )

        # Add a virtual guest's host name if available
        self._add_fact_to_fingerprint(
            source, "virtual_host_name", fact, "virtual_host_name", fingerprint
        )
        self._add_fact_to_fingerprint(
            source, "virtual_host_uuid", fact, "virtual_host_uuid", fingerprint
        )

        is_virtualized = default_getter(fact, "is_virtualized", "")
        metadata_source = "is_virtualized"
        name = default_getter(fact, "hostname", "")
        if is_virtualized:
            infrastructure_type = SystemFingerprint.VIRTUALIZED
        elif is_virtualized is False:
            infrastructure_type = SystemFingerprint.BARE_METAL
        else:
            infrastructure_type = SystemFingerprint.UNKNOWN
        if name.startswith("virt-who-") and name.endswith(
            tuple(["-" + str(num) for num in range(1, 10)])
        ):
            infrastructure_type = SystemFingerprint.HYPERVISOR
            metadata_source = "hostname"
        self._add_fact_to_fingerprint(
            source,
            metadata_source,
            fact,
            "infrastructure_type",
            fingerprint,
            fact_value=infrastructure_type,
        )
        # Satellite specific facts
        self._add_fact_to_fingerprint(
            source, "cores", fact, "cpu_core_count", fingerprint
        )
        self._add_fact_to_fingerprint(
            source, "num_sockets", fact, "cpu_socket_count", fingerprint
        )

        # Raw fact for system_creation_date
        reg_time = fact.get("registration_time")
        if reg_time:
            reg_time = strip_suffix(reg_time, " UTC")
        self._add_fact_to_fingerprint(
            source,
            "registration_time",
            fact,
            "registration_time",
            fingerprint,
            fact_value=reg_time,
        )

        last_checkin = fact.get("last_checkin_time")
        if last_checkin:
            last_checkin = self._multi_format_dateparse(
                source,
                "last_checkin_time",
                last_checkin,
                ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S %z"],
            )

        self._add_fact_to_fingerprint(
            source,
            "last_checkin_time",
            fact,
            "system_last_checkin_date",
            fingerprint,
            fact_value=last_checkin,
        )

        self._add_entitlements_to_fingerprint(source, "entitlements", fact, fingerprint)
        self._add_products_to_fingerprint(source, fact, fingerprint)

        return fingerprint

    def _process_openshift_fact(self, source, fact):
        """Process a fact and convert to a fingerprint.

        :param source: The source that provided this fact.
        :param facts: fact to process
        :returns: fingerprint produced from fact
        """
        fingerprint = {
            META_DATA_KEY: {},
            ENTITLEMENTS_KEY: [],
            PRODUCTS_KEY: [],
        }
        self._add_fact_to_fingerprint(source, "node__name", fact, "name", fingerprint)
        self._add_fact_to_fingerprint(
            source, "node__capacity__cpu", fact, "cpu_count", fingerprint
        )
        self._add_fact_to_fingerprint(
            source,
            "node__architecture",
            fact,
            "architecture",
            fingerprint,
            fact_formatter=formatters.convert_architecture,
        )
        self._add_fact_to_fingerprint(
            source, "node__machine_id", fact, "etc_machine_id", fingerprint
        )
        self._add_fact_to_fingerprint(
            source,
            "node__addresses",
            fact,
            "ip_addresses",
            fingerprint,
            fact_formatter=ocp_formatters.extract_ip_addresses,
        )
        self._add_fact_to_fingerprint(
            source,
            "node__creation_timestamp",
            fact,
            "creation_timestamp",
            fingerprint,
        )
        self._add_fact_to_fingerprint(
            source,
            "node__cluster_uuid",
            fact,
            "vm_cluster",
            fingerprint,
        )

        self._add_fact_to_fingerprint(
            source,
            "node__labels",
            fact,
            "system_role",
            fingerprint,
            fact_formatter=ocp_formatters.infer_node_role,
        )

        return fingerprint

    def _process_ansible_fact(self, source, fact):
        """Generate fingerprints for ansible controller facts."""
        fingerprint = {
            META_DATA_KEY: {},
            ENTITLEMENTS_KEY: [],
            PRODUCTS_KEY: [],
        }
        self._add_fact_to_fingerprint(
            source,
            "instance_details__system_name",
            fact,
            "name",
            fingerprint,
        )
        self._add_fact_to_fingerprint(
            source,
            "instance_details__version",
            fact,
            "os_version",
            fingerprint,
        )
        return fingerprint

    def _multi_format_dateparse(self, source, raw_fact_key, date_value, patterns):
        """Attempt multiple patterns for strptime.

        :param source: The source that provided this fact.
        :param raw_fact_key: fact key with date.
        :param date_value: date value to parse
        :returns: parsed date
        """
        if date_value:
            raw_date_value = strip_suffix(date_value, " UTC")
            date_error = None
            for pattern in patterns:
                try:
                    date_date_value = datetime.strptime(raw_date_value, pattern)
                    return date_date_value.date()
                except ValueError as error:
                    date_error = error

            self.scan_task.log_message(
                f"Fingerprinter ({source['source_type']}, {source['source_name']}) - "
                f"Could not parse date for {raw_fact_key}. "
                f"Unsupported date format: '{raw_date_value}'. Error: {date_error}",
                log_level=logging.ERROR,
            )
        return None
