"""OpenShift Prometheus metrics definitions and utilities."""

OCP_PROMETHEUS_METRICS = {
    "node_metrics": {
        "attributes": [
            "instance",
            "label_node_hyperthread_enabled",
            "label_node_role_kubernetes_io_master",
        ],
        "query": """
count by(instance,
         label_node_hyperthread_enabled,
         label_node_role_kubernetes_io_master)
(max
    by(node, instance,
             label_node_hyperthread_enabled,
             label_node_role_kubernetes_io_master)
    (cluster:cpu_core_node_labels)
)
""",
    }
}


def retrieve_cluster_metrics(ocp_client):
    """Execute Prometheus queries and return the Cluster metrics."""
    cluster_metrics = {}
    for name, metric in OCP_PROMETHEUS_METRICS.items():
        raw_result = ocp_client.metrics_query(metric["query"])
        result = []
        for item in raw_result:
            query_item = {}
            for attr in metric["attributes"]:
                query_item[attr] = item.get(attr, None)
            result.append(query_item)
        cluster_metrics[name] = result
    return cluster_metrics
