# Copyright (c) 2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Initial processing of the shell output from the dmi role."""
import logging

from scanner.network.processing import process

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ProcessDmiSystemUuid(process.Processor):
    """Process the dmi system uuid."""

    # pylint: disable=too-few-public-methods
    KEY = "dmi_system_uuid"

    DEPS = ["internal_dmi_system_uuid"]
    REQUIRE_DEPS = False

    @staticmethod
    def process(output, dependencies):
        """Pass the output back through."""
        dmi_system_uuid = dependencies.get("internal_dmi_system_uuid")
        if dmi_system_uuid and dmi_system_uuid.get("rc") == 0:
            result = dmi_system_uuid.get("stdout_lines")
            if result:
                dmi_system_uuid = result[0]
                if result[0] == "" and len(result) > 1:
                    dmi_system_uuid = result[1]
                if len(dmi_system_uuid) <= 36:
                    return dmi_system_uuid
                logger.warning(
                    "dmi_system_uuid is invalid because "
                    "its length is greater than 36.  "
                    "dmi_system_uuid value: %s",
                    dmi_system_uuid,
                )
        return ""
