"""Serializer for aggregate report."""

from rest_framework import serializers

from api.models import AggregateReport


class ResultsSerializer(serializers.ModelSerializer):
    """Serializer for the results portion of the Aggregate Report."""

    class Meta:
        """Serializer configuration."""

        model = AggregateReport
        fields = [
            "ansible_hosts_all",
            "ansible_hosts_in_database",
            "ansible_hosts_in_jobs",
            "instances_hypervisor",
            "instances_not_redhat",
            "instances_physical",
            "instances_unknown",
            "instances_virtual",
            "jboss_eap_cores_physical",
            "jboss_eap_cores_virtual",
            "jboss_eap_instances",
            "jboss_ws_cores_physical",
            "jboss_ws_cores_virtual",
            "jboss_ws_instances",
            "openshift_cores",
            "openshift_operators_by_name",
            "openshift_operators_by_kind",
            "os_by_name_and_version",
            "socket_pairs",
            "system_creation_date_average",
            "vmware_hosts",
            "vmware_vm_to_host_ratio",
            "vmware_vms",
            "openshift_cluster_instances",
            "openshift_node_instances",
        ]


class DiagnosticsSerializer(serializers.ModelSerializer):
    """Serializer for the diagnostics portion of the Aggregate Report."""

    class Meta:
        """Serializer configuration."""

        model = AggregateReport
        fields = [
            "inspect_result_status_failed",
            "inspect_result_status_success",
            "inspect_result_status_unknown",
            "inspect_result_status_unreachable",
            "missing_cpu_core_count",
            "missing_cpu_socket_count",
            "missing_name",
            "missing_pem_files",
            "missing_system_creation_date",
            "missing_system_purpose",
        ]


class AggregateReportSerializer(serializers.ModelSerializer):
    """Aggregate Report Serializer."""

    results = ResultsSerializer(many=False, source="*")
    diagnostics = DiagnosticsSerializer(many=False, source="*")

    class Meta:
        """Serializer configuration."""

        model = AggregateReport
        fields = ["results", "diagnostics"]
