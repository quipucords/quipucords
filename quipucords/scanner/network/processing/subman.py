"""Initial processing of the shell output from the subman role."""

import logging

from scanner.network.processing import process

logger = logging.getLogger(__name__)

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
            if not entitlement:
                # Skip emtpy lines.
                continue
            try:
                name, entitlement_id = entitlement.split(" - ")
                entitlement_dict = {"name": name, "entitlement_id": entitlement_id}
                entitlements_data.append(entitlement_dict)
            except ValueError as e:
                # .split may fail on unexpected outputs in the stdout_lines.
                # We should log this as an error but keep trying other lines.
                logger.error(e)
        return entitlements_data
