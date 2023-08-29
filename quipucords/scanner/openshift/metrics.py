"""OpenShift Prometheus metrics definitions and utilities."""

OCP_PROMETHEUS_METRICS = {
    "node_metrics": {
        "attributes": [
            "instance",
            "label_node_hyperthread_enabled",
            "label_node_role_kubernetes_io_master",
            "package",
        ],
        "query": """
            group by(
                instance,
                label_node_hyperthread_enabled,
                label_node_role_kubernetes_io_master,
                package
            )  (cluster:cpu_core_node_labels)
            """,
    }
}


def retrieve_cluster_metrics(ocp_client, metric):
    """Execute a Prometheus query and return the Cluster metrics."""
    result = []
    for item in ocp_client.metrics_query(metric["query"]):
        result_item = {}
        for attr in metric["attributes"]:
            result_item[attr] = item.get(attr, None)
        result.append(result_item)
    return result
