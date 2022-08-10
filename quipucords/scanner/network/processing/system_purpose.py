# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Initial processing of the system purpose role."""

import json
import logging

from scanner.network.processing import process

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# pylint: disable=too-few-public-methods


class ProcessSystemPurpose(process.Processor):
    """Process the system_purpose_json fact."""

    KEY = "system_purpose_json"

    @staticmethod
    def process(output, dependencies=None):
        """Pass the output back through."""
        system_purpose_str = output.get("stdout", None)
        if system_purpose_str:
            try:
                system_purpose_dict = json.loads(system_purpose_str)
                return system_purpose_dict
            except json.decoder.JSONDecodeError as error:
                logger.warning("system_purpose was not valid JSON.  Error: %s", error)
                return None
        return None
