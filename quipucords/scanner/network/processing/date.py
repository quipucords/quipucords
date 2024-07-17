"""Initial processing of the shell output from the date role."""

import logging

from scanner.network.processing import process
from scanner.network.processing.util import get_line

logger = logging.getLogger(__name__)

# #### Processors ####


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
