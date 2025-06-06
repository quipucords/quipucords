"""
Model definition and calculation logic for the aggregate report.

The logic here is kind of messy because we do not surface all the necessary
details into individual fields in the normalized/de-duped SystemFingerprint model.
To minimize the number of iterations and trips back to the database, we iterate
through all SystemFingerprint rows once and conditionally tally various fields,
and then we iterate through all RawFact rows (via InspectGroup) and conditionally
tally various fields that only exist there. This iteration logic could be
simplified to use Django query aggregates if we stored more individual fields in
SystemFingerprint or some other even flatter data structure that DOES NOT use
JSONField-like fields that require additional special logic. Until that exists,
the logic here will remain somewhat long and complex.

Much of this logic could be made more readable by naively breaking up individual
fields into their own "sum(map(lambda ...))" one-liners or multiple smaller Django
aggregate queries. However, that would mean iterating over the rows multiple times,
and that would likely cause execution time to grow linearly with the number of hosts
and facts, and that may get too costly too quickly. The current ugly implementation
iterates through all the facts exactly once to minimize expected execution time.
"""

import logging
from collections import defaultdict
from collections.abc import Iterable
from math import ceil

from django.db import models

from api.common.models import BaseModel
from api.deployments_report.model import Product, SystemFingerprint
from api.inspectresult.model import InspectResult
from api.report.model import Report
from constants import DataSources
from utils.datetime import average_date

logger = logging.getLogger(__name__)

UNKNOWN: str = "unknown"  # placeholder string for missing names/versions/kinds.


class AggregateReport(BaseModel):
    """Results of the aggregate report."""

    report = models.OneToOneField(
        "Report", models.CASCADE, related_name="aggregate_report", null=False
    )

    # Note the lack of special reporting needs for Satellite or RHACS here.
    # At the time of this writing, Justin says this is correct and we have none.

    ansible_hosts_all = models.PositiveIntegerField(default=0, blank=True, null=True)
    ansible_hosts_in_database = models.PositiveIntegerField(
        default=0, blank=True, null=True
    )
    ansible_hosts_in_jobs = models.PositiveIntegerField(
        default=0, blank=True, null=True
    )
    inspect_result_status_failed = models.PositiveIntegerField(
        default=0, blank=True, null=True
    )
    inspect_result_status_success = models.PositiveIntegerField(
        default=0, blank=True, null=True
    )
    inspect_result_status_unknown = models.PositiveIntegerField(
        default=0, blank=True, null=True
    )
    inspect_result_status_unreachable = models.PositiveIntegerField(
        default=0, blank=True, null=True
    )
    instances_hypervisor = models.PositiveIntegerField(default=0, blank=True, null=True)
    instances_not_redhat = models.PositiveIntegerField(default=0, blank=True, null=True)
    instances_physical = models.PositiveIntegerField(default=0, blank=True, null=True)
    instances_unknown = models.PositiveIntegerField(default=0, blank=True, null=True)
    instances_virtual = models.PositiveIntegerField(default=0, blank=True, null=True)
    jboss_eap_cores_physical = models.FloatField(default=0.0, blank=True, null=True)
    jboss_eap_cores_virtual = models.FloatField(default=0.0, blank=True, null=True)
    jboss_eap_instances = models.PositiveIntegerField(default=0, blank=True, null=True)
    jboss_ws_cores_physical = models.FloatField(default=0.0, blank=True, null=True)
    jboss_ws_cores_virtual = models.FloatField(default=0.0, blank=True, null=True)
    jboss_ws_instances = models.PositiveIntegerField(default=0, blank=True, null=True)
    missing_cpu_core_count = models.PositiveIntegerField(
        default=0, blank=True, null=True
    )
    missing_cpu_socket_count = models.PositiveIntegerField(
        default=0, blank=True, null=True
    )
    missing_name = models.PositiveIntegerField(default=0, blank=True, null=True)
    missing_pem_files = models.PositiveIntegerField(default=0, blank=True, null=True)
    missing_system_creation_date = models.PositiveIntegerField(
        default=0, blank=True, null=True
    )
    missing_system_purpose = models.PositiveIntegerField(
        default=0, blank=True, null=True
    )
    openshift_cores = models.PositiveIntegerField(default=0, blank=True, null=True)
    openshift_operators_by_name = models.JSONField(null=False, default=dict)
    openshift_operators_by_kind = models.JSONField(null=False, default=dict)
    os_by_name_and_version = models.JSONField(null=False, default=dict)
    socket_pairs = models.PositiveIntegerField(default=0, blank=True, null=True)
    system_creation_date_average = models.DateField(blank=True, null=True)
    vmware_hosts = models.PositiveIntegerField(default=0, blank=True, null=True)
    vmware_vm_to_host_ratio = models.FloatField(default=0, blank=True, null=True)
    vmware_vms = models.PositiveIntegerField(default=0, blank=True, null=True)

    # Note: The following attributes come exclusively from raw facts.
    # For now, that's our only option, and these are required outputs.
    # TODO Refactor how we populate these when we restructure the underlying data.
    openshift_cluster_instances = models.PositiveIntegerField(
        default=0, blank=True, null=True
    )
    openshift_node_instances = models.PositiveIntegerField(
        default=0, blank=True, null=True
    )


def get_aggregate_report_by_report_id(report_id: int) -> AggregateReport | None:
    """Build and get the aggregate report for the given report ID."""
    try:
        report = Report.objects.get(pk=report_id)
        aggregated = build_aggregate_report(report.id)
        return aggregated
    except Report.DoesNotExist:
        return None


def _aggregate_from_system_fingerprints(  # noqa: C901,PLR0912,PLR0915
    aggregated: AggregateReport, fingerprints: Iterable[SystemFingerprint]
) -> None:
    """
    Populate the AggregateReport object with data from the given SystemFingerprints.

    TODO Try to break up some to this to reduce the noqa: C901,PLR0912,PLR0915.
    """
    # Note: importing jboss_eap and jboss_web_server here as to avoid the circular
    # import error since api.models now imports AggregateReport and those jboss
    # modules also import Product from api.models.
    from fingerprinter import jboss_eap, jboss_web_server

    os_by_name_and_version = defaultdict(lambda: defaultdict(int))
    system_creation_dates = []
    vmware_vms_by_host = defaultdict(list)

    for fingerprint in fingerprints:
        # Yes, we want *all* OS name/version combos regardless of `is_redhat`.
        # This means output may include non-RHEL distros (e.g. Ubuntu, Debian).
        # Note: Ansible sources are fingerprinted to store the Ansible controller
        # version (e.g. "4.4.4") in SystemFingerprint.os_version, and that can
        # results strange in output here like {"unknown": {"4.4.4": 1}}.
        # See also: FingerprintTaskRunner._process_ansible_fact.
        # Those versions may look weird, but Justin says to keep them all.
        os_by_name_and_version[fingerprint.os_name or UNKNOWN][
            fingerprint.os_version or UNKNOWN
        ] += 1

        source_types = [source.get("source_type") for source in fingerprint.sources]
        has_network_source = DataSources.NETWORK in source_types
        has_satellite_source = DataSources.SATELLITE in source_types
        has_vcenter_source = DataSources.VCENTER in source_types
        has_openshift_source = DataSources.OPENSHIFT in source_types

        if not (fingerprint.is_redhat or has_openshift_source or has_satellite_source):
            # For all other fingerprint facts we aggregate below here, we only want
            # to count them if we positively identified Red Hat during fingerprinting.
            # We treat everything found by OpenShift or Satellite to be "is_redhat=True"
            # here even if the "is_redhat" attribute was not set on the fingerprint.
            aggregated.instances_not_redhat += 1
            continue

        if not fingerprint.cpu_core_count and (
            has_network_source or has_satellite_source
        ):
            # Only network and satellite sources set this fact,
            # and we don't want to penalize others for not having it.
            aggregated.missing_cpu_core_count += 1

        if not fingerprint.cpu_socket_count:
            aggregated.missing_cpu_socket_count += 1

        if not fingerprint.name:
            aggregated.missing_name += 1

        if not fingerprint.system_creation_date:
            aggregated.missing_system_creation_date += 1
        else:
            system_creation_dates.append(fingerprint.system_creation_date)

        cpu_core_count = fingerprint.cpu_core_count or 0

        # For now (forever?) we *do not* care to count Scan.JBOSS_FUSE.
        # If we don't care about it, then why bother collecting the data?
        # Justin says FUSE will be phased out mid-2024.
        # TODO Remove *all* other API/model/etc. code related to FUSE.
        product_presences = {
            product.name: bool(product.presence == Product.PRESENT)
            for product in fingerprint.products.all()
        }
        jboss_eap_present = product_presences.get(jboss_eap.PRODUCT, False)
        jboss_ws_present = product_presences.get(jboss_web_server.PRODUCT, False)
        jboss_eap_cpu_core_count = cpu_core_count if jboss_eap_present else 0
        jboss_ws_cpu_core_count = cpu_core_count if jboss_ws_present else 0

        if fingerprint.infrastructure_type == SystemFingerprint.VIRTUALIZED:
            aggregated.instances_virtual += 1
            aggregated.jboss_eap_cores_virtual += jboss_eap_cpu_core_count
            aggregated.jboss_ws_cores_virtual += jboss_ws_cpu_core_count
        elif fingerprint.infrastructure_type == SystemFingerprint.BARE_METAL:
            aggregated.instances_physical += 1
            aggregated.jboss_eap_cores_physical += jboss_eap_cpu_core_count
            aggregated.jboss_ws_cores_physical += jboss_ws_cpu_core_count
        elif fingerprint.infrastructure_type == SystemFingerprint.HYPERVISOR:
            aggregated.instances_hypervisor += 1
        else:
            aggregated.instances_unknown += 1
        aggregated.jboss_eap_instances += 1 if jboss_eap_present else 0
        aggregated.jboss_ws_instances += 1 if jboss_ws_present else 0

        if fingerprint.cpu_socket_count:
            # This may look strange, but Justin assures us that it is correct.
            # Some products are sold specifically with this per-two-CPU-sockets math.
            # Try not to think too hard about this.
            aggregated.socket_pairs += ceil(fingerprint.cpu_socket_count / 2)

        if has_network_source:
            if not fingerprint.system_purpose:
                aggregated.missing_system_purpose += 1
            if not fingerprint.redhat_certs:
                aggregated.missing_pem_files += 1
        if has_openshift_source:
            if fingerprint.cpu_count:
                aggregated.openshift_cores += fingerprint.cpu_count
        if has_vcenter_source:
            vmware_cluster = fingerprint.vm_cluster
            vmware_host = fingerprint.virtual_host_uuid
            if vmware_cluster and vmware_host:
                vmware_vms_by_host[vmware_cluster].append(vmware_host)

    aggregated.os_by_name_and_version = {
        os_name: dict(os_versions)
        for os_name, os_versions in os_by_name_and_version.items()
    }

    aggregated.system_creation_date_average = average_date(system_creation_dates)

    if vmware_vms_by_host:
        # By collecting *all* the hosts in vmware_vms_by_host, we can effectively
        # deduplicate them here. We collected the hosts and VMs by their names,
        # not their UUIDs, which means that if two actually different hosts or VMs
        # have the same name (e.g. "localhost"), then we might under-count them here.
        # Justin said this is correct and consistent with how other aspects of our
        # business count usage by simple hostnames.
        vmware_vm_count = sum(len(set(items)) for items in vmware_vms_by_host.values())
        vmware_host_count = len(vmware_vms_by_host)
        aggregated.vmware_vms = vmware_vm_count
        aggregated.vmware_vm_to_host_ratio = vmware_vm_count / vmware_host_count
        aggregated.vmware_hosts = vmware_host_count


def _aggregate_from_inspect_results(
    aggregated: AggregateReport, inspect_results: Iterable[InspectResult]
) -> None:
    """Populate the AggregateReport object with data from the given InspectResults."""
    for inspect_result in inspect_results:
        if inspect_result.status == InspectResult.SUCCESS:
            aggregated.inspect_result_status_success += 1
        elif inspect_result.status == InspectResult.FAILED:
            aggregated.inspect_result_status_failed += 1
        elif inspect_result.status == InspectResult.UNREACHABLE:
            aggregated.inspect_result_status_unreachable += 1
        else:
            aggregated.inspect_result_status_unknown += 1


def _aggregate_from_raw_facts(
    aggregated: AggregateReport,
    grouped_facts: Iterable[tuple[str, Iterable[dict]]],
) -> None:
    """
    Populate the AggregateReport object with data from the given raw facts.

    Due to set operations to determine unique Ansible hosts, this function
    should always be called *once* with *all* facts related to a given Report.

    Do we really want to build reports directly from raw facts?
    No, but we don't currently have any better options for some data points.
    TODO Stop building reports based on raw facts when we have better models.
    """
    ansible_hosts_in_database = []
    ansible_hosts_in_jobs = []
    openshift_operators_by_name = defaultdict(int)
    openshift_operators_by_kind = defaultdict(int)

    for source_type, raw_facts in grouped_facts:
        for raw_fact in raw_facts:
            if source_type == DataSources.ANSIBLE:
                # hosts.name and jobs.unique_hosts are simply hostnames, and
                # unlike UUIDs, their uniqueness is not guaranteed.
                # This means if multiple hosts identify themselves with
                # the same name (e.g. "localhost") then we will under-count
                # them. Justin said this is correct and consistent with how
                # other aspects of our business count usage by simple hostnames.
                ansible_hosts_in_database.extend(
                    [
                        host.get("name")
                        for host in raw_fact.get("hosts", [])
                        if host.get("name")
                    ]
                )
                ansible_hosts_in_jobs.extend(
                    raw_fact.get("jobs", {}).get("unique_hosts", [])
                )
            elif source_type == DataSources.OPENSHIFT:
                if raw_fact.get("cluster", {}).get("kind") == "cluster":
                    aggregated.openshift_cluster_instances += 1
                elif raw_fact.get("node", {}).get("kind") == "node":
                    aggregated.openshift_node_instances += 1
                for operator in raw_fact.get("operators", []):
                    openshift_operators_by_kind[operator.get("kind", UNKNOWN)] += 1
                    openshift_operators_by_name[operator.get("name", UNKNOWN)] += 1

    ansible_hosts_in_database = set(ansible_hosts_in_database)
    ansible_hosts_in_jobs = set(ansible_hosts_in_jobs)
    ansible_hosts_all = ansible_hosts_in_database | ansible_hosts_in_jobs

    aggregated.ansible_hosts_all = len(ansible_hosts_all)
    aggregated.ansible_hosts_in_database = len(ansible_hosts_in_database)
    aggregated.ansible_hosts_in_jobs = len(ansible_hosts_in_jobs)

    aggregated.openshift_operators_by_kind.update(openshift_operators_by_kind)
    aggregated.openshift_operators_by_name.update(openshift_operators_by_name)


def build_aggregate_report(
    report_id: int, force_build: bool = False
) -> AggregateReport:
    """Aggregate various totals from the facts related to the given report ID."""
    report = Report.objects.get(pk=report_id)
    try:
        aggregated = AggregateReport.objects.get(report_id=report_id)
        if report.updated_at <= aggregated.updated_at and not force_build:
            return aggregated
        # If we are here, then we need to update the aggregate report.
        # To be safe and eliminate any risk of double counting, delete the old
        # report object and start fresh after exiting this try block.
        aggregated.delete()
    except AggregateReport.DoesNotExist:
        pass

    aggregated = AggregateReport.objects.create(report_id=report_id)

    # Note that `aggregated` is treated as a pass-by-reference here and is updated
    # directly in these functions instead of returning a new instance.
    _aggregate_from_system_fingerprints(
        aggregated, report.deployment_report.system_fingerprints.all()
    )
    _aggregate_from_inspect_results(
        aggregated,
        (
            result
            for group in report.inspect_groups.all()
            for result in group.inspect_results.all()
        ),
    )

    # TODO Try to query RawFacts directly instead of using report.sources.
    # That should be faster than going through the InspectGroupQuerySet. We would still
    # need to decode the RawFact.value JSON, but we could filter to only get only the
    # RawFact.name matches we actually need here, and decoding their .value JSON might
    # be faster than InspectGroupQuerySet decoding *all* of the rows.
    _aggregate_from_raw_facts(
        aggregated,
        (
            (inspect_group.get("source_type"), inspect_group["facts"])
            for inspect_group in report.sources.all()
        ),
    )

    aggregated.save()
    # Make sure aggregated reflects the database's declared schema
    # i.e. floats stored as int to be represented as such.
    aggregated.refresh_from_db()
    return aggregated
