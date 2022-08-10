# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Initial processing of the shell output from the date role."""

import logging

from scanner.network.processing import process
from scanner.network.processing.util import get_line

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# pylint: disable=too-few-public-methods

# #### Processors ####


class ProcessDateDate(process.Processor):
    """Process the date fact."""

    KEY = "date_date"

    @staticmethod
    def process(output, dependencies=None):
        """Pass the output back through."""
        return get_line(output["stdout_lines"])


class ProcessDateFilesystemCreate(process.Processor):
    """Process the date filesystem create fact."""

    KEY = "date_filesystem_create"

    @staticmethod
    def process(output, dependencies=None):
        """Pass the output back through."""
        return get_line(output["stdout_lines"])


class ProcessDateMachineId(process.Processor):
    """Process the date machine id fact."""

    KEY = "date_machine_id"

    @staticmethod
    def process(output, dependencies=None):
        """Pass the output back through."""
        return get_line(output["stdout_lines"])


class ProcessDateYumHistory(process.Processor):
    """Process the date machine id fact."""

    KEY = "date_yum_history"
    RETURN_CODE_ANY = True

    @staticmethod
    def process(output, dependencies=None):
        """Pass the output back through."""
        result = output.get("stdout_lines")
        if isinstance(result, list):
            result = [line for line in result if line]
            if result:
                return result[0]
        return process.NO_DATA
