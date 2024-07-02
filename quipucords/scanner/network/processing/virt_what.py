"""Initial processing of the shell output from the virt_what role."""

import logging

from scanner.network.processing.process import RC, ProcessedResult, Processor

logger = logging.getLogger(__name__)


class ProcessVirtWhat(Processor):
    """Process the virt_what fact."""

    KEY = "virt_what"

    @staticmethod
    def process(output, dependencies=None):
        """Process virt_what fact output."""
        return ProcessVirtWhat._process(output)

    @classmethod
    def _process(cls, output):
        """Process virt_what fact output."""
        exit_code = output.get(RC)
        if exit_code != 0:
            # Ignore virt-what output if it has a non-zero exit code.
            # See also: https://issues.redhat.com/browse/DISCOVERY-427
            return ProcessedResult(return_code=exit_code, value=[])

        value = [
            line.strip() for line in output.get("stdout_lines", []) if line.strip()
        ]
        return ProcessedResult(return_code=exit_code, value=value)
