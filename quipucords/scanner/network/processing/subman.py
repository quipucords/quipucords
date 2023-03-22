"""Initial processing of the shell output from the subman role."""

import logging

from scanner.network.processing import process

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

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
