#
# Copyright (c) 2017-2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""ScanTask used for network connection discovery."""
import json
import logging
import uuid
from datetime import datetime

from api.models import (DeploymentsReport,
                        Product,
                        ScanJob,
                        ScanTask,
                        Source,
                        SystemFingerprint)
from api.serializers import (SystemFingerprintSerializer)

from fingerprinter.jboss_brms import detect_jboss_brms
from fingerprinter.jboss_eap import detect_jboss_eap
from fingerprinter.jboss_fuse import detect_jboss_fuse
from fingerprinter.jboss_web_server import detect_jboss_ws
from fingerprinter.utils import strip_suffix

from rest_framework.serializers import DateField

from scanner.task import ScanTaskRunner

# pylint: disable=too-many-lines

# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


# Keys used to de-duplicate against other network sources
NETWORK_IDENTIFICATION_KEYS = ['subscription_manager_id',
                               'bios_uuid']

# Keys used to de-duplicate against other VCenter sources
VCENTER_IDENTIFICATION_KEYS = ['vm_uuid']

# Keys used to de-duplicate against other satellite sources
SATELLITE_IDENTIFICATION_KEYS = ['subscription_manager_id']

# Keys used to de-duplicate against across sources
NETWORK_SATELLITE_MERGE_KEYS = [
    ('subscription_manager_id', 'subscription_manager_id'),
    ('mac_addresses', 'mac_addresses')]
NETWORK_VCENTER_MERGE_KEYS = [
    ('bios_uuid', 'vm_uuid'),
    ('mac_addresses', 'mac_addresses')]

FINGERPRINT_GLOBAL_ID_KEY = 'FINGERPRINT_GLOBAL_ID'

META_DATA_KEY = 'metadata'
ENTITLEMENTS_KEY = 'entitlements'
PRODUCTS_KEY = 'products'
NAME_KEY = 'name'
PRESENCE_KEY = 'presence'
SOURCES_KEY = 'sources'

# keys are in reverse order of accuracy (last most accurate)
# (date_key, date_pattern)
RAW_DATE_KEYS = \
    [('date_yum_history', ['%Y-%m-%d']),
     ('date_filesystem_create', ['%Y-%m-%d']),
     ('date_anaconda_log', ['%Y-%m-%d']),
     ('registration_time', ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S %z']),
     ('date_machine_id', ['%Y-%m-%d'])]


class FingerprintTaskRunner(ScanTaskRunner):
    """ConnectTaskRunner system connection capabilities.

    Attempts connections to a source using a list of credentials
    and gathers the set of successes (host/ip, credential) and
    failures (host/ip).
    """

    # pylint: disable=too-many-locals,no-self-use
    # pylint: disable=too-many-arguments,too-few-public-methods
    def __init__(self, scan_job, scan_task):
        """Set context for task execution.

        :param scan_job: the scan job that contains this task
        :param scan_task: the scan task model for this task
        to store results
        """
        super().__init__(scan_job, scan_task)
        self.scan_task = scan_task

    def check_for_interrupt(self, manager_interrupt):
        """Process the details report.

        :param manager_interrupt: Signal to indicate job is canceled
        :return status, message indicating if shutdown should occur.
            ScanTask.RUNNING indicates process should continue
        """
        if manager_interrupt.value == ScanJob.JOB_TERMINATE_CANCEL:
            manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
            error_message = 'Scan canceled'
            manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
            return error_message, ScanTask.CANCELED

        if manager_interrupt.value == ScanJob.JOB_TERMINATE_PAUSE:
            manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
            error_message = 'Scan paused'
            manager_interrupt.value = ScanJob.JOB_TERMINATE_ACK
            return error_message, ScanTask.PAUSED
        return 'keep going', ScanTask.RUNNING

    def run(self, manager_interrupt):
        """Scan network range and attempt connections."""
        # Make sure job is not cancelled or paused
        interrupt_message, interrupt_status = self.check_for_interrupt(
            manager_interrupt)
        if interrupt_status != ScanTask.RUNNING:
            return interrupt_message, interrupt_status

        details_report = self.scan_task.details_report

        # remove results from previous interrupted scan
        deployment_report = details_report.deployment_report
        if not deployment_report:
            deployment_report = DeploymentsReport()
            deployment_report.save()

            # Set the report ids.  Right now they are deployment report id
            # but they do not have to
            deployment_report.report_id = deployment_report.id
            deployment_report.save()

            details_report.deployment_report = deployment_report
            details_report.report_id = deployment_report.id
            details_report.save()
        else:
            # remove partial results
            self.scan_task.log_message(
                'REMOVING PARTIAL RESULTS - deleting %d '
                'fingerprints from previous scan'
                % len(deployment_report.system_fingerprints().all()))
            deployment_report.system_fingerprints().all().delete()
            deployment_report.save()

        try:
            message, status = self._process_fact_collection(
                manager_interrupt, details_report)

            interrupt_message, interrupt_status = self.check_for_interrupt(
                manager_interrupt)
            if interrupt_status != ScanTask.RUNNING:
                return interrupt_message, interrupt_status

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
            error_message = 'Fact collection %d failed'\
                ' to be processed.' % details_report.id

            self.scan_task.log_message(
                '%s' % (error_message), log_level=logging.ERROR)
            self.scan_task.log_message('%s:%s' % (
                error.__class__.__name__, error), log_level=logging.ERROR)
            raise error

    def _process_fact_collection(self, manager_interrupt, details_report):
        """Process the details report.

        :param manager_interrupt: Signal to indicate job is canceled
        :param details_report: DetailsReport that was saved
        :param scan_task: Task that is running this merge
        :returns: Status message and status
        """
        # pylint: disable=unused-argument
        self.scan_task.log_message('START DEDUPLICATION')

        # Invoke ENGINE to create fingerprints from facts
        fingerprints_list = self._process_sources(details_report)

        self.scan_task.log_message('END DEDUPLICATION')

        number_valid = 0
        number_invalid = 0
        self.scan_task.log_message('START FINGERPRINT PERSISTENCE')
        status_count = 0
        total_count = len(fingerprints_list)
        deployment_report = details_report.deployment_report
        date_field = DateField()
        final_fingerprint_list = []
        for fingerprint_dict in fingerprints_list:
            status_count += 1
            name = fingerprint_dict.get('name', 'unknown')
            os_release = fingerprint_dict.get('os_release', 'unknown')
            self.scan_task.log_message(
                'FINGERPRINT %d of %d SAVED - Fingerprint '
                '(name=%s, os_release=%s)' %
                (status_count, total_count, name, os_release))

            if status_count % 100 == 0:
                interrupt_message, interrupt_status = self.check_for_interrupt(
                    manager_interrupt)
                if interrupt_status != ScanTask.RUNNING:
                    return interrupt_message, interrupt_status
            fingerprint_dict['deployment_report'] = deployment_report.id
            serializer = SystemFingerprintSerializer(data=fingerprint_dict)
            if serializer.is_valid():
                number_valid += 1
                serializer.save()
                fingerprint_dict.pop('deployment_report')
                # Serialize the date
                for field in SystemFingerprint.DATE_FIELDS:
                    if fingerprint_dict.get(field, None):
                        fingerprint_dict[field] = date_field.to_representation(
                            fingerprint_dict.get(field))
                final_fingerprint_list.append(fingerprint_dict)
            else:
                number_invalid += 1
                self.scan_task.log_message(
                    'Invalid fingerprint: %s' %
                    fingerprint_dict, log_level=logging.ERROR)
                self.scan_task.log_message(
                    'Fingerprint errors: %s' %
                    serializer.errors, log_level=logging.ERROR)
            self.scan_task.log_message('Fingerprints (report id=%d): %s' %
                                       (details_report.id, fingerprint_dict),
                                       log_level=logging.DEBUG)

        # Mark completed because engine has process raw facts
        status = ScanTask.COMPLETED
        status_message = 'success'
        if final_fingerprint_list:
            deployment_report.status = DeploymentsReport.STATUS_COMPLETE
        else:
            status_message = 'FAILED to create report id=%d - '\
                'produced no valid fingerprints ' % (
                    deployment_report.report_id)
            self.scan_task.log_message(status_message, log_level=logging.ERROR)
            deployment_report.status = DeploymentsReport.STATUS_FAILED
            status = ScanTask.FAILED
        deployment_report.cached_json = json.dumps(final_fingerprint_list)
        deployment_report.save()

        self.scan_task.log_message('RESULTS (report id=%d) -  '
                                   '(valid fingerprints=%d, '
                                   'invalid fingerprints=%d)' %
                                   (deployment_report.report_id,
                                    number_valid,
                                    number_invalid))

        self.scan_task.log_message('END FINGERPRINT PERSISTENCE')

        return status_message, status

    def _process_sources(self, details_report):
        """Process facts and convert to fingerprints.

        :param details_report: DetailsReport containing raw facts
        :returns: list of fingerprints for all systems (all scans)
        """
        # pylint: disable=too-many-statements
        network_fingerprints = []
        vcenter_fingerprints = []
        satellite_fingerprints = []

        total_source_count = len(details_report.get_sources())
        self.scan_task.log_message(
            '%d sources to process' % total_source_count)
        source_count = 0
        for source in details_report.get_sources():
            source_count += 1
            source_type = source.get('source_type')
            source_name = source.get('source_name')
            self.scan_task.log_message('PROCESSING Source %d of %d - '
                                       '(name=%s, type=%s, server=%s)' % (
                                           source_count,
                                           total_source_count,
                                           source_name,
                                           source_type,
                                           source.get('server_id')))
            source_fingerprints = self._process_source(source)
            if source_type == Source.NETWORK_SOURCE_TYPE:
                network_fingerprints += source_fingerprints
            elif source_type == Source.VCENTER_SOURCE_TYPE:
                vcenter_fingerprints += source_fingerprints
            elif source_type == Source.SATELLITE_SOURCE_TYPE:
                satellite_fingerprints += source_fingerprints

            self.scan_task.log_message(
                'SOURCE FINGERPRINTS - '
                '%d %s fingerprints' % (
                    len(source_fingerprints),
                    source_type))

            self.scan_task.log_message(
                'TOTAL FINGERPRINT COUNT - '
                'Fingerprints '
                '(network=%d, satellite=%d, vcenter=%d, total=%d)' %
                (
                    len(network_fingerprints),
                    len(satellite_fingerprints),
                    len(vcenter_fingerprints),
                    len(network_fingerprints) +
                    len(satellite_fingerprints) +
                    len(vcenter_fingerprints)))

        # Deduplicate network fingerprints
        self.scan_task.log_message(
            'NETWORK DEDUPLICATION by keys %s' %
            NETWORK_IDENTIFICATION_KEYS)
        before_count = len(network_fingerprints)
        network_fingerprints = self._remove_duplicate_fingerprints(
            NETWORK_IDENTIFICATION_KEYS,
            network_fingerprints)
        self.scan_task.log_message(
            'NETWORK DEDUPLICATION RESULT - '
            '(before=%d, after=%d)' %
            (before_count, len(network_fingerprints)))

        # Deduplicate satellite fingerprints
        self.scan_task.log_message(
            'SATELLITE DEDUPLICATION by keys %s' %
            SATELLITE_IDENTIFICATION_KEYS)
        before_count = len(satellite_fingerprints)
        satellite_fingerprints = self._remove_duplicate_fingerprints(
            SATELLITE_IDENTIFICATION_KEYS,
            satellite_fingerprints)
        self.scan_task.log_message(
            'SATELLITE DEDUPLICATION RESULT - '
            '(before=%d, after=%d)' %
            (before_count, len(satellite_fingerprints)))

        # Deduplicate vcenter fingerprints
        self.scan_task.log_message(
            'VCENTER DEDUPLICATION by keys %s' %
            VCENTER_IDENTIFICATION_KEYS)
        before_count = len(vcenter_fingerprints)
        vcenter_fingerprints = self._remove_duplicate_fingerprints(
            VCENTER_IDENTIFICATION_KEYS,
            vcenter_fingerprints)
        self.scan_task.log_message(
            'VCENTER DEDUPLICATION RESULT - '
            '(before=%d, after=%d)' %
            (before_count, len(vcenter_fingerprints)))

        self.scan_task.log_message(
            'TOTAL FINGERPRINT COUNT - ''Fingerprints '
            '(network=%d, satellite=%d, vcenter=%d, total=%d)' %
            (
                len(network_fingerprints),
                len(satellite_fingerprints),
                len(vcenter_fingerprints),
                len(network_fingerprints) +
                len(satellite_fingerprints) +
                len(vcenter_fingerprints)))

        # Merge network and satellite fingerprints
        self.scan_task.log_message(
            'NETWORK and SATELLITE DEDUPLICATION '
            'by keys pairs [(network_key, satellite_key)]=%s' %
            NETWORK_SATELLITE_MERGE_KEYS)
        number_network_before = len(network_fingerprints)
        number_satellite_before = len(satellite_fingerprints)
        number_vcenter_before = len(vcenter_fingerprints)
        total_before = number_network_before + \
            number_satellite_before + number_vcenter_before
        self.scan_task.log_message(
            'NETWORK and SATELLITE DEDUPLICATION '
            'START COUNT - (network=%d, satellite=%d, '
            'vcenter=%d, total=%d)' % (
                number_network_before,
                number_satellite_before,
                number_vcenter_before,
                total_before))

        _, all_fingerprints = \
            self._merge_fingerprints_from_source_types(
                NETWORK_SATELLITE_MERGE_KEYS,
                network_fingerprints,
                satellite_fingerprints)
        number_after = len(all_fingerprints)
        self.scan_task.log_message(
            'NETWORK and SATELLITE DEDUPLICATION '
            'END COUNT - (combined_network_satellite=%d,'
            ' vcenter=%d, total=%d)' % (
                number_after,
                number_vcenter_before,
                number_after + number_vcenter_before))

        # Merge network and vcenter fingerprints
        reverse_priority_keys = {'cpu_count', 'infrastructure_type'}
        self.scan_task.log_message(
            'NETWORK-SATELLITE and VCENTER DEDUPLICATION'
            ' by keys pairs '
            '[(network_satellite_key, vcenter_key)]=%s' %
            NETWORK_VCENTER_MERGE_KEYS)
        self.scan_task.log_message(
            'NETWORK-SATELLITE and VCENTER DEDUPLICATION'
            ' by reverse priority keys '
            '(we trust vcenter more than network/satellite): %s' %
            reverse_priority_keys)

        number_network_satellite_before = len(all_fingerprints)
        number_vcenter_before = len(vcenter_fingerprints)
        total_before = number_network_satellite_before + number_vcenter_before
        self.scan_task.log_message(
            'NETWORK-SATELLITE and VCENTER DEDUPLICATION '
            'START COUNT - (combined_network_satellite=%d, '
            'vcenter=%d, total=%d)' % (
                number_network_satellite_before,
                number_vcenter_before,
                total_before))

        _, all_fingerprints = \
            self._merge_fingerprints_from_source_types(
                NETWORK_VCENTER_MERGE_KEYS,
                all_fingerprints,
                vcenter_fingerprints,
                reverse_priority_keys=reverse_priority_keys)
        number_after = len(all_fingerprints)
        self.scan_task.log_message(
            'NETWORK-SATELLITE and VCENTER DEDUPLICATION '
            'END COUNT - (total=%d)' % (
                number_after))

        self._post_process_merged_fingerprints(all_fingerprints)
        return all_fingerprints

    def _post_process_merged_fingerprints(self, fingerprints):
        """Normalize cross source fingerprint values.

        This is required when values need cross source complex
        logic.
        :param fingerprints: final list of fingerprints
        associated with facts.
        """
        self.scan_task.log_message(
            'POST MERGE PROCESSING BEGIN - computing system creation time')
        for fingerprint in fingerprints:
            fingerprint[SOURCES_KEY] = list(fingerprint[SOURCES_KEY].values())
            self._compute_system_creation_time(fingerprint)
        self.scan_task.log_message(
            'POST MERGE PROCESSING END - computing system creation time')

    def _compute_system_creation_time(self, fingerprint):
        """Normalize cross source fingerprint values.

        This is required when values need cross source complex
        logic.
        :param fingerprints: final list of fingerprints
        associated with facts.
        """
        # keys are in reverse order of accuracy (last most accurate)
        system_creation_date = None
        system_creation_date_metadata = None
        for date_key, date_pattern in RAW_DATE_KEYS:
            date_value = fingerprint.pop(date_key, None)
            if date_value is not None:
                system_creation_date_metadata = fingerprint[META_DATA_KEY].pop(
                    date_key, None)
                system_creation_date = self._multi_format_dateparse(
                    system_creation_date_metadata,
                    date_key,
                    date_value,
                    date_pattern)

        if system_creation_date is not None:
            fingerprint['system_creation_date'] = system_creation_date
            fingerprint[META_DATA_KEY]['system_creation_date'] = \
                system_creation_date_metadata

    def _process_source(self, source):
        """Process facts and convert to fingerprints.

        :param source: The JSON source information
        :returns: fingerprints produced from facts
        """
        fingerprints = []
        for fact in source['facts']:
            fingerprint = None
            server_id = source.get('server_id')
            source_type = source.get('source_type')
            source_name = source.get('source_name')
            if source_type == Source.NETWORK_SOURCE_TYPE:
                fingerprint = self._process_network_fact(source, fact)
            elif source_type == Source.VCENTER_SOURCE_TYPE:
                fingerprint = self._process_vcenter_fact(source, fact)
            elif source_type == Source.SATELLITE_SOURCE_TYPE:
                fingerprint = self._process_satellite_fact(source, fact)
            else:
                self.scan_task.log_message.error(
                    'Could not process source, '
                    'unknown source type: %s' %
                    source_type, log_level=logging.ERROR)

            if fingerprint is not None:
                fingerprint[SOURCES_KEY] = \
                    {'%s+%s' % (server_id, source_name): {
                        'server_id': server_id,
                        'source_type': source_type,
                        'source_name': source_name}}
                fingerprints.append(fingerprint)

        return fingerprints

    def _merge_fingerprints_from_source_types(self, merge_keys_list,
                                              base_list,
                                              merge_list,
                                              reverse_priority_keys=None):
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
            key_merged_count, result, to_merge = \
                self._merge_matching_fingerprints(
                    key_tuple[0], result, key_tuple[1], to_merge,
                    reverse_priority_keys=reverse_priority_keys)
            number_merged += key_merged_count

        # Add remaining as they didn't match anything (no merge)
        result = result + to_merge
        return number_merged, result

    def _merge_matching_fingerprints(self, base_key,
                                     base_list,
                                     candidate_key,
                                     candidate_list,
                                     reverse_priority_keys=None):
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
        # pylint: disable=too-many-locals,consider-iterating-dictionary
        base_dict, base_no_key = self._create_index_for_fingerprints(
            base_key, base_list)
        candidate_dict, candidate_no_key = self._create_index_for_fingerprints(
            candidate_key, candidate_list)

        # Initialize lists with values that cannot be compared
        base_match_list = []
        candidate_no_match_list = []

        number_merged = 0
        # Match candidate to base fingerprint using index key
        for candidate_index_key, candidate_fingerprint in \
                candidate_dict.items():
            # For each overlay fingerprint check for matching base fingerprint
            # using candidate_index_key.  Remove so value is not in
            # left-over set
            base_value = base_dict.pop(candidate_index_key, None)
            if base_value:
                # candidate_index_key == base_key so merge
                merged_value = self._merge_fingerprint(
                    base_value,
                    candidate_fingerprint,
                    reverse_priority_keys=reverse_priority_keys)
                number_merged += 1

                # Add merged value to key
                base_match_list.append(merged_value)
            else:
                # Could not merge, so add to not merged list
                candidate_no_match_list.append(candidate_fingerprint)

        # Merge base items without key, matched, and remainder
        # who did not match
        base_result_list = base_no_key + \
            base_match_list + list(base_dict.values())
        base_result_list = self._remove_duplicate_fingerprints(
            [FINGERPRINT_GLOBAL_ID_KEY], base_result_list, True)

        # Merge candidate items without key list with those that didn't match
        candidate_no_match_list = candidate_no_key + candidate_no_match_list
        candidate_no_match_list = self._remove_duplicate_fingerprints(
            [FINGERPRINT_GLOBAL_ID_KEY], candidate_no_match_list, True)

        return number_merged, base_result_list, candidate_no_match_list

    def _remove_duplicate_fingerprints(self, id_key_list,
                                       fingerprint_list,
                                       remove_key=False):
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

        result_list = fingerprint_list[:]
        for id_key in id_key_list:
            unique_dict = {}
            no_global_id_list = []
            for fingerprint in result_list:
                unique_id_value = fingerprint.get(id_key)
                if unique_id_value:
                    # Add or update fingerprint value
                    unique_dict[unique_id_value] = fingerprint
                else:
                    no_global_id_list.append(fingerprint)

            result_list = no_global_id_list + list(unique_dict.values())

            # Strip id key from fingerprints if requested
            if remove_key:
                for fingerprint in result_list:
                    unique_id_value = fingerprint.get(id_key)
                    if unique_id_value:
                        del fingerprint[id_key]

        return result_list

    def _create_index_for_fingerprints(self, id_key,
                                       fingerprint_list,
                                       create_global_id=True):
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
                    if result_by_key.get(id_key_value) is None:
                        result_by_key[id_key_value] = value_dict
                    else:
                        number_duplicates += 1
            else:
                key_not_found_list.append(value_dict)
        if number_duplicates:
            self.scan_task.log_message(
                '_create_index_for_fingerprints - '
                'Potential lost fingerprint due to duplicate %s: %d.' %
                (id_key, number_duplicates), log_level=logging.DEBUG)
        return result_by_key, key_not_found_list

    # pylint: disable=too-many-branches, too-many-locals
    def _merge_fingerprint(self, priority_fingerprint,
                           to_merge_fingerprint,
                           reverse_priority_keys=None):
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
        priority_keys = set(priority_fingerprint.keys())
        to_merge_keys = set(to_merge_fingerprint.keys())

        # Merge keys from to_merge into priority.  These
        # are keys not in priority or have a reverse priority.
        keys_to_add_list = to_merge_keys - priority_keys
        if reverse_priority_keys is not None and \
                isinstance(reverse_priority_keys, set):
            keys_to_add_list = keys_to_add_list | reverse_priority_keys
        keys_to_add_list = list(keys_to_add_list)
        if META_DATA_KEY in keys_to_add_list:
            keys_to_add_list.remove(META_DATA_KEY)

        for fact_key in keys_to_add_list:
            to_merge_fact = to_merge_fingerprint.get(fact_key)
            if to_merge_fact:
                priority_fingerprint[META_DATA_KEY][fact_key] = \
                    to_merge_fingerprint[META_DATA_KEY][fact_key]
                priority_fingerprint[fact_key] = to_merge_fact

        # merge sources
        priority_sources = priority_fingerprint[SOURCES_KEY]
        to_merge_sources = to_merge_fingerprint[SOURCES_KEY]

        for source in to_merge_sources:
            if source not in priority_sources.keys():
                priority_sources[source] = to_merge_sources[source]

        if to_merge_fingerprint.get(ENTITLEMENTS_KEY):
            if ENTITLEMENTS_KEY not in priority_fingerprint:
                priority_fingerprint[ENTITLEMENTS_KEY] = []
            priority_fingerprint[ENTITLEMENTS_KEY] += \
                to_merge_fingerprint.get(ENTITLEMENTS_KEY, [])

        if to_merge_fingerprint.get(PRODUCTS_KEY):
            if PRODUCTS_KEY not in priority_fingerprint:
                priority_fingerprint[PRODUCTS_KEY] = \
                    to_merge_fingerprint.get(PRODUCTS_KEY, [])
            else:
                priority_prod_dict = {}
                priority_prod = priority_fingerprint.get(PRODUCTS_KEY, [])
                to_merge_prod = to_merge_fingerprint.get(PRODUCTS_KEY, [])
                for prod in priority_prod:
                    priority_prod_dict[prod[NAME_KEY]] = prod
                for prod in to_merge_prod:
                    merge_prod = priority_prod_dict.get(prod[NAME_KEY])
                    presence = merge_prod.get(PRESENCE_KEY)
                    if (merge_prod and presence == Product.ABSENT and
                            prod.get(PRESENCE_KEY) != Product.ABSENT):
                        priority_prod_dict[prod[NAME_KEY]] = prod
                    elif merge_prod is None:
                        priority_prod_dict[prod[NAME_KEY]] = prod
                priority_fingerprint[PRODUCTS_KEY] = list(
                    priority_prod_dict.values())

        return priority_fingerprint

    def _add_fact_to_fingerprint(self, source,
                                 raw_fact_key,
                                 raw_fact,
                                 fingerprint_key,
                                 fingerprint,
                                 fact_value=None):
        """Create the fingerprint fact and metadata.

        :param source: Source used to gather raw facts.
        :param raw_fact_key: Raw fact key used to obtain value
        :param raw_fact: Raw fact used used to obtain value
        :param fingerprint_key: Key used to store fingerprint
        :param fingerprint: dict containing all fingerprint facts
        this fact.
        :param fact_value: Used when values are computed from
        raw facts instead of direct access.
        """
        # pylint: disable=too-many-arguments
        actual_fact_value = None
        if fact_value is not None:
            actual_fact_value = fact_value
        elif raw_fact.get(raw_fact_key) is not None:
            actual_fact_value = raw_fact.get(raw_fact_key)
        if fingerprint_key == 'mac_addresses':
            if isinstance(actual_fact_value, list):
                actual_fact_value = list(map(lambda x: x.lower(),
                                             actual_fact_value))

        # Remove empty string values
        if isinstance(actual_fact_value, str) and not actual_fact_value:
            actual_fact_value = None

        if actual_fact_value is not None:
            fingerprint[fingerprint_key] = actual_fact_value
            fingerprint[META_DATA_KEY][fingerprint_key] = {
                'server_id': source['server_id'],
                'source_name': source['source_name'],
                'source_type': source['source_type'],
                'raw_fact_key': raw_fact_key
            }

    def _add_products_to_fingerprint(self, source,
                                     raw_fact,
                                     fingerprint):
        """Create the fingerprint products with fact and metadata.

        :param source: Source used to gather raw facts.
        :param raw_fact: Raw fact used used to obtain value
        :param fingerprint: dict containing all fingerprint facts
        this fact.
        """
        eap = detect_jboss_eap(source, raw_fact)
        fuse = detect_jboss_fuse(source, raw_fact)
        brms = detect_jboss_brms(source, raw_fact)
        jws = detect_jboss_ws(source, raw_fact)
        fingerprint['products'] = [eap, fuse, brms, jws]

    def _add_entitlements_to_fingerprint(self, source,
                                         raw_fact_key,
                                         raw_fact,
                                         fingerprint):
        """Create the fingerprint entitlements with fact and metadata.

        :param source: Source used to gather raw facts.
        :param raw_fact_key: Raw fact key used to obtain value
        :param raw_fact: Raw fact used used to obtain value
        :param fingerprint: dict containing all fingerprint facts
        this fact.
        """
        # pylint: disable=too-many-arguments
        actual_fact_value = None
        if raw_fact.get(raw_fact_key) is not None:
            actual_fact_value = raw_fact.get(raw_fact_key)
        entitlements = []
        if actual_fact_value is not None and \
                isinstance(actual_fact_value, list):
            for entitlement in actual_fact_value:
                add = False
                f_ent = {}
                if entitlement.get('name'):
                    f_ent['name'] = entitlement.get('name')
                    add = True
                if entitlement.get('entitlement_id'):
                    f_ent['entitlement_id'] = entitlement.get('entitlement_id')
                    add = True
                if add:
                    f_ent[META_DATA_KEY] = {
                        'server_id': source['server_id'],
                        'source_name': source['source_name'],
                        'source_type': source['source_type'],
                        'raw_fact_key': raw_fact_key
                    }
                    entitlements.append(f_ent)

            fingerprint[ENTITLEMENTS_KEY] = entitlements
        else:
            fingerprint[ENTITLEMENTS_KEY] = entitlements

    # pylint: disable=R0915
    def _process_network_fact(self, source, fact):
        """Process a fact and convert to a fingerprint.

        :param source: The source that provided this fact.
        :param facts: fact to process
        :returns: fingerprint produced from fact
        """
        fingerprint = {META_DATA_KEY: {}}

        # Common facts
        self._add_fact_to_fingerprint(source, 'uname_hostname',
                                      fact, 'name', fingerprint)
        self._add_fact_to_fingerprint(source, 'uname_processor', fact,
                                      'architecture', fingerprint)

        # Red Hat facts
        self._add_fact_to_fingerprint(source,
                                      'redhat_packages_gpg_num_rh_packages',
                                      fact, 'redhat_package_count',
                                      fingerprint)
        self._add_fact_to_fingerprint(source,
                                      'redhat_packages_certs', fact,
                                      'redhat_certs', fingerprint)
        self._add_fact_to_fingerprint(source, 'redhat_packages_gpg_is_redhat',
                                      fact, 'is_redhat', fingerprint)

        # Set OS information
        self._add_fact_to_fingerprint(source, 'etc_release_name',
                                      fact, 'os_name', fingerprint)
        self._add_fact_to_fingerprint(source, 'etc_release_version',
                                      fact, 'os_version', fingerprint)
        self._add_fact_to_fingerprint(source, 'etc_release_release',
                                      fact, 'os_release', fingerprint)

        # Set ip address from either network or vcenter
        self._add_fact_to_fingerprint(source, 'ifconfig_ip_addresses',
                                      fact, 'ip_addresses', fingerprint)

        # Set mac address from either network or vcenter
        self._add_fact_to_fingerprint(source, 'ifconfig_mac_addresses',
                                      fact, 'mac_addresses', fingerprint)

        # Set CPU facts
        self._add_fact_to_fingerprint(source, 'cpu_count',
                                      fact, 'cpu_count', fingerprint)

        # Network scan specific facts
        # Set bios UUID
        self._add_fact_to_fingerprint(source, 'dmi_system_uuid',
                                      fact, 'bios_uuid', fingerprint)

        # Set subscription manager id
        self._add_fact_to_fingerprint(source, 'subman_virt_uuid',
                                      fact, 'subscription_manager_id',
                                      fingerprint)

        # System information
        self._add_fact_to_fingerprint(source, 'cpu_socket_count',
                                      fact, 'cpu_socket_count', fingerprint)
        self._add_fact_to_fingerprint(source, 'cpu_core_count',
                                      fact, 'cpu_core_count', fingerprint)

        # Determine system_creation_date
        self._add_fact_to_fingerprint(source, 'date_machine_id',
                                      fact, 'date_machine_id', fingerprint)
        self._add_fact_to_fingerprint(source, 'date_anaconda_log',
                                      fact, 'date_anaconda_log',
                                      fingerprint)
        self._add_fact_to_fingerprint(source, 'date_filesystem_create',
                                      fact, 'date_filesystem_create',
                                      fingerprint)
        self._add_fact_to_fingerprint(source, 'date_yum_history',
                                      fact, 'date_yum_history', fingerprint)

        if fact.get('connection_timestamp'):
            last_checkin = self._multi_format_dateparse(
                source,
                'connection_timestamp',
                fact['connection_timestamp'],
                ['%Y%m%d%H%M%S'])
            self._add_fact_to_fingerprint(source, 'connection_timestamp',
                                          fact, 'system_last_checkin_date',
                                          fingerprint,
                                          fact_value=last_checkin)

        # Determine if running on VM or bare metal
        virt_what_type = fact.get('virt_what_type')
        virt_type = fact.get('virt_type')
        if virt_what_type or virt_type:
            if virt_what_type == 'bare metal':
                self._add_fact_to_fingerprint(
                    source, 'virt_what_type', fact, 'infrastructure_type',
                    fingerprint, fact_value=SystemFingerprint.BARE_METAL)
            elif virt_type:
                self._add_fact_to_fingerprint(
                    source, 'virt_type', fact, 'infrastructure_type',
                    fingerprint, fact_value='virtualized')
            else:
                # virt_what_type is not bare metal or None
                # (since both cannot be)
                self._add_fact_to_fingerprint(
                    source, 'virt_what_type', fact, 'infrastructure_type',
                    fingerprint, fact_value='unknown')
        else:
            self._add_fact_to_fingerprint(
                source, 'virt_what_type/virt_type', fact,
                'infrastructure_type',
                fingerprint, fact_value='unknown')

        # Determine if VM facts
        self._add_fact_to_fingerprint(source, 'virt_type', fact,
                                      'virtualized_type', fingerprint)

        self._add_entitlements_to_fingerprint(source, 'subman_consumed',
                                              fact, fingerprint)
        self._add_products_to_fingerprint(source, fact, fingerprint)

        return fingerprint

    def _process_vcenter_fact(self, source, fact):
        """Process a fact and convert to a fingerprint.

        :param source: The source that provided this fact.
        :param facts: fact to process
        :returns: fingerprint produced from fact
        """
        # pylint: disable=too-many-branches

        fingerprint = {META_DATA_KEY: {}}

        # Common facts
        # Set name
        self._add_fact_to_fingerprint(
            source, 'vm.name', fact, 'name', fingerprint)

        self._add_fact_to_fingerprint(source, 'vm.os', fact,
                                      'os_release', fingerprint)
        vcenter_os_release = fact.get('vm.os', '')
        is_redhat = False
        if vcenter_os_release != '':
            rhel_os_releases = ['red hat enterprise linux', 'rhel']
            for rhel_release in rhel_os_releases:
                if rhel_release in vcenter_os_release.lower():
                    is_redhat = True
                    break
        self._add_fact_to_fingerprint(source, 'vm.os',
                                      fact, 'is_redhat', fingerprint,
                                      fact_value=is_redhat)
        self._add_fact_to_fingerprint(source, 'vcenter_source', fact,
                                      'infrastructure_type', fingerprint,
                                      fact_value='virtualized')
        self._add_fact_to_fingerprint(source, 'vm.mac_addresses',
                                      fact, 'mac_addresses', fingerprint)
        self._add_fact_to_fingerprint(source, 'vm.ip_addresses',
                                      fact, 'ip_addresses', fingerprint)
        self._add_fact_to_fingerprint(source, 'vm.cpu_count',
                                      fact, 'cpu_count', fingerprint)
        self._add_fact_to_fingerprint(source, 'uname_processor', fact,
                                      'architecture', fingerprint)

        # VCenter specific facts
        self._add_fact_to_fingerprint(source, 'vm.state', fact,
                                      'vm_state', fingerprint)
        self._add_fact_to_fingerprint(source, 'vm.uuid', fact,
                                      'vm_uuid', fingerprint)

        if fact.get('vm.last_check_in'):
            last_checkin = self._multi_format_dateparse(
                source, 'vm.last_check_in',
                fact['vm.last_check_in'],
                ['%Y-%m-%d %H:%M:%S'])
            self._add_fact_to_fingerprint(source, 'vm.last_check_in',
                                          fact, 'system_last_checkin_date',
                                          fingerprint,
                                          fact_value=last_checkin)

        self._add_fact_to_fingerprint(source, 'vm.dns_name', fact,
                                      'vm_dns_name', fingerprint)
        self._add_fact_to_fingerprint(source, 'vm.host.name',
                                      fact, 'vm_host', fingerprint)
        self._add_fact_to_fingerprint(source, 'vm.host.cpu_count',
                                      fact, 'vm_host_socket_count',
                                      fingerprint)
        self._add_fact_to_fingerprint(source, 'vm.datacenter',
                                      fact, 'vm_datacenter', fingerprint)
        self._add_fact_to_fingerprint(source, 'vm.cluster', fact,
                                      'vm_cluster', fingerprint)

        fingerprint[ENTITLEMENTS_KEY] = []
        fingerprint[PRODUCTS_KEY] = []

        return fingerprint

    def _process_satellite_fact(self, source, fact):
        """Process a fact and convert to a fingerprint.

        :param source: The source that provided this fact.
        :param facts: fact to process
        :returns: fingerprint produced from fact
        """
        # pylint: disable=too-many-branches
        rhel_versions = {'4Server': 'Red Hat Enterprise Linux 4 Server',
                         '5Server': 'Red Hat Enterprise Linux 5 Server',
                         '6Server': 'Red Hat Enterprise Linux 6 Server',
                         '7Server': 'Red Hat Enterprise Linux 7 Server',
                         '8Server': 'Red Hat Enterprise Linux 8 Server'}

        fingerprint = {META_DATA_KEY: {}}

        # Common facts
        self._add_fact_to_fingerprint(
            source, 'hostname', fact, 'name', fingerprint)

        self._add_fact_to_fingerprint(source, 'os_name', fact,
                                      'os_name', fingerprint)
        # Get the os name
        satellite_os_name = fact.get('os_name')
        is_redhat = False
        rhel_version = None
        # if the os name is none
        if not satellite_os_name:
            # grab the os release
            satellite_os_release = fact.get('os_release', '')
            if satellite_os_release in rhel_versions.keys():
                # if the os release is a rhel version
                # 1. set the is redhat fact to true and add it to fingerprint
                # 2. set the rhel version to the rhel versions value
                is_redhat = True
                rhel_version = rhel_versions[satellite_os_release]
            self._add_fact_to_fingerprint(source, 'os_release',
                                          fact, 'is_redhat', fingerprint,
                                          fact_value=is_redhat)
        else:
            # if the os name indicates redhat, set is_redhat to true
            rhel_os_names = ['rhel', 'redhat', 'redhatenterpriselinux']
            if satellite_os_name.lower().replace(' ', '') in rhel_os_names:
                is_redhat = True
            self._add_fact_to_fingerprint(source, 'os_name',
                                          fact, 'is_redhat', fingerprint,
                                          fact_value=is_redhat)
        if rhel_version:
            self._add_fact_to_fingerprint(source, 'os_release', fact,
                                          'os_release', fingerprint,
                                          fact_value=rhel_version)
        else:
            self._add_fact_to_fingerprint(source, 'os_release', fact,
                                          'os_release', fingerprint)

        self._add_fact_to_fingerprint(source, 'os_version', fact,
                                      'os_version', fingerprint)

        self._add_fact_to_fingerprint(source, 'mac_addresses',
                                      fact, 'mac_addresses', fingerprint)
        self._add_fact_to_fingerprint(source, 'ip_addresses', fact,
                                      'ip_addresses', fingerprint)

        self._add_fact_to_fingerprint(source, 'cores', fact,
                                      'cpu_count', fingerprint)
        self._add_fact_to_fingerprint(source, 'architecture', fact,
                                      'architecture', fingerprint)

        # Common network/satellite
        self._add_fact_to_fingerprint(source, 'uuid', fact,
                                      'subscription_manager_id', fingerprint)
        self._add_fact_to_fingerprint(source, 'virt_type', fact,
                                      'virtualized_type', fingerprint)

        is_virtualized = fact.get('is_virtualized')
        infrastructure_type = None
        if is_virtualized:
            infrastructure_type = 'virtualized'
        elif is_virtualized is False:
            infrastructure_type = SystemFingerprint.BARE_METAL
        if infrastructure_type:
            self._add_fact_to_fingerprint(source, 'is_virtualized', fact,
                                          'infrastructure_type', fingerprint,
                                          fact_value=infrastructure_type)
        # Satellite specific facts
        self._add_fact_to_fingerprint(source, 'cores', fact,
                                      'cpu_core_count', fingerprint)
        self._add_fact_to_fingerprint(source, 'num_sockets', fact,
                                      'cpu_socket_count', fingerprint)

        # Raw fact for system_creation_date
        reg_time = fact.get('registration_time')
        if reg_time:
            reg_time = strip_suffix(reg_time, ' UTC')
            self._add_fact_to_fingerprint(source, 'registration_time', fact,
                                          'registration_time', fingerprint,
                                          fact_value=reg_time)

        last_checkin = fact.get('last_checkin_time')
        if last_checkin:
            last_checkin = \
                self._multi_format_dateparse(source,
                                             'last_checkin_time',
                                             last_checkin,
                                             ['%Y-%m-%d %H:%M:%S',
                                              '%Y-%m-%d %H:%M:%S %z'])

            self._add_fact_to_fingerprint(source, 'last_checkin_time',
                                          fact, 'system_last_checkin_date',
                                          fingerprint,
                                          fact_value=last_checkin)

        self._add_entitlements_to_fingerprint(source, 'entitlements',
                                              fact, fingerprint)
        self._add_products_to_fingerprint(source, fact, fingerprint)

        return fingerprint

    def _multi_format_dateparse(self,
                                source,
                                raw_fact_key,
                                date_value,
                                patterns):
        """Attempt multiple patterns for strptime.

        :param source: The source that provided this fact.
        :param raw_fact_key: fact key with date.
        :param date_value: date value to parse
        :returns: parsed date
        """
        if date_value:
            raw_date_value = strip_suffix(date_value, ' UTC')
            date_error = None
            for pattern in patterns:
                try:
                    date_date_value = datetime.strptime(
                        raw_date_value, pattern)
                    return date_date_value.date()
                except ValueError as error:
                    date_error = error

            self.scan_task.log_message(
                'Fingerprinter (%s, %s) - '
                'Could not parse date for %s. '
                'Unsupported date format: \'%s\'. Error: %s' %
                (source['source_type'],
                 source['source_name'],
                 raw_fact_key,
                 raw_date_value,
                 date_error),
                log_level=logging.ERROR)
        return None
