"""Initial processing of the shell output from the ifconfig role."""

from scanner.network.processing import process

INET_PREFIXES = ["inet addr:", "inet "]
INET6_PREFIXES = ["inet6 "]


class ProcessIPAddresses(process.Processor):
    """Process the ip addresses from ifconfig."""

    KEY = "ifconfig_ip_addresses"

    @staticmethod
    def process(output, dependencies=None):
        """Pass the output back through."""
        result = []
        lines = [line.strip() for line in output["stdout_lines"]]
        for line in lines:
            for prefix in INET_PREFIXES:
                if line.startswith(prefix):
                    ip_line = line[len(prefix) :].split()[0]
                    if ip_line != "127.0.0.1":
                        result.append(ip_line)
                    break
            for prefix in INET6_PREFIXES:
                if line.startswith(prefix):
                    ipv6_line = line[len(prefix) :].split()[0]
                    if ipv6_line != "::1":
                        result.append(ipv6_line)
                    break
        return list(set(result))


class ProcessMacAddresses(process.Processor):
    """Process the mac addresses from ifconfig."""

    KEY = "ifconfig_mac_addresses"

    @staticmethod
    def process(output, dependencies=None):
        """Pass the output back through."""
        result = []
        addresses = output.get("stdout_lines", [])
        for address in addresses:
            if address:
                result.append(address)
        return list(set(result))
