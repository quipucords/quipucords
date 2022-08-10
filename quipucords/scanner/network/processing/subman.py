# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Initial processing of the shell output from the subman role."""

import logging

from scanner.network.processing import process

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# pylint: disable=too-few-public-methods

# #### Processors ####


class ProcessSubmanConsumed(process.Processor):
    """Process the subman_consumed fact."""

    KEY = "subman_consumed"

    @staticmethod
    def process(output, dependencies=None):
        """Pass the output back through."""
        entitlements_data = []
        entitlements = output.get("stdout_lines", [])
        for entitlement in entitlements:
            if entitlement:
                name, entitlement_id = entitlement.split(" - ")
                entitlement_dict = {"name": name, "entitlement_id": entitlement_id}
                entitlements_data.append(entitlement_dict)
        return entitlements_data
