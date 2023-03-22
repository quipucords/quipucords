"""Initial processing of the system purpose role."""

import json
import logging

from scanner.network.processing import process

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


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
