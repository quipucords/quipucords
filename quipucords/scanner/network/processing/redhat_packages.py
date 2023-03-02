"""Initial processing of the shell output from the redhat_packages role."""

import logging

from scanner.network.processing import process

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# pylint: disable=too-few-public-methods

# #### Processors ####


class ProcessRedHatPackagesCerts(process.Processor):
    """Process the redhat packages certs."""

    KEY = "redhat_packages_certs"

    @staticmethod
    def process(output, dependencies=None):
        """Pass the output back through."""
        if output.get("rc", True):
            return ""
        certs = output.get("stdout")
        if certs:
            if certs[-1] == ";":
                certs = certs[:-1]
        return certs
