"""Fingerprint formatters for OpenShift."""


def extract_ip_addresses(addresses):
    """Extract only ip addresses from list of addresses."""
    ip_addresses = []
    for element in addresses:
        if "ip" in element.get("type").lower():
            ip_addresses.append(element.get("address"))
    return ip_addresses


def infer_node_role(labels: dict):
    """Infer node role based on its labels dict."""
    node_roles = []
    for role in ["worker", "master", "control-plane"]:
        role_label = f"node-role.kubernetes.io/{role}"
        if role_label in labels.keys():
            node_roles.append(role)
    return "/".join(node_roles)
