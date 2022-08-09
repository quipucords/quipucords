# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Initial processing of the shell output from the ifconfig role."""

from scanner.network.processing import process


INET_PREFIXES = ["inet addr:", "inet "]

# pylint: disable=too-few-public-methods


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
