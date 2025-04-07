"""View for aggregate report."""

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from api.aggregate_report.model import get_aggregate_report_by_report_id


class ResultsSerializer(serializers.Serializer):
    """Serializer for the results portion of the Aggregate Report."""

    ansible_hosts_all = serializers.IntegerField(default=0, min_value=0)
    ansible_hosts_in_database = serializers.IntegerField(default=0, min_value=0)
    ansible_hosts_in_jobs = serializers.IntegerField(default=0, min_value=0)
    instances_hypervisor = serializers.IntegerField(default=0, min_value=0)
    instances_not_redhat = serializers.IntegerField(default=0, min_value=0)
    instances_physical = serializers.IntegerField(default=0, min_value=0)
    instances_unknown = serializers.IntegerField(default=0, min_value=0)
    instances_virtual = serializers.IntegerField(default=0, min_value=0)
    jboss_eap_cores_physical = serializers.FloatField(default=0.0, min_value=0)
    jboss_eap_cores_virtual = serializers.FloatField(default=0.0, min_value=0)
    jboss_eap_instances = serializers.IntegerField(default=0, min_value=0)
    jboss_ws_cores_physical = serializers.FloatField(default=0.0, min_value=0)
    jboss_ws_cores_virtual = serializers.FloatField(default=0.0, min_value=0)
    jboss_ws_instances = serializers.IntegerField(default=0, min_value=0)
    openshift_cores = serializers.IntegerField(default=0, min_value=0)
    openshift_operators_by_name = serializers.JSONField(default=dict)
    openshift_operators_by_kind = serializers.JSONField(default=dict)
    os_by_name_and_version = serializers.JSONField(default=dict)
    socket_pairs = serializers.IntegerField(default=0, min_value=0)
    system_creation_date_average = serializers.DateField()
    vmware_hosts = serializers.IntegerField(default=0, min_value=0)
    vmware_vm_to_host_ratio = serializers.FloatField(default=0)
    vmware_vms = serializers.IntegerField(default=0, min_value=0)
    openshift_cluster_instances = serializers.IntegerField(default=0, min_value=0)
    openshift_node_instances = serializers.IntegerField(default=0, min_value=0)


class DiagnosticsSerializer(serializers.Serializer):
    """Serializer for the diagnostics portion of the Aggregate Report."""

    inspect_result_status_failed = serializers.IntegerField(default=0, min_value=0)
    inspect_result_status_success = serializers.IntegerField(default=0, min_value=0)
    inspect_result_status_unknown = serializers.IntegerField(default=0, min_value=0)
    inspect_result_status_unreachable = serializers.IntegerField(default=0, min_value=0)
    missing_cpu_core_count = serializers.IntegerField(default=0, min_value=0)
    missing_cpu_socket_count = serializers.IntegerField(default=0, min_value=0)
    missing_name = serializers.IntegerField(default=0, min_value=0)
    missing_pem_files = serializers.IntegerField(default=0, min_value=0)
    missing_system_creation_date = serializers.IntegerField(default=0, min_value=0)
    missing_system_purpose = serializers.IntegerField(default=0, min_value=0)


class AggregateReportSerializer(serializers.Serializer):
    """Aggregate Report Serializer."""

    results = ResultsSerializer(many=False)
    diagnostics = DiagnosticsSerializer(many=False)


@extend_schema(responses=AggregateReportSerializer)
@api_view(["GET"])
def aggregate_report(request, report_id: int) -> Response:
    """Lookup and return a details system report."""
    report_dict = get_aggregate_report_by_report_id(report_id)
    if report_dict:
        return Response(report_dict)
    raise NotFound
