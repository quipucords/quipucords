"""Initial processing of the system purpose role."""

import json
import logging
import re

from scanner.network.processing import process

logger = logging.getLogger(__name__)


class ProcessSystemPurpose(process.Processor):
    """Process the system_purpose_json fact."""

    KEY = "system_purpose_json"

    @staticmethod
    def process(output, dependencies=None):
        """Pass the output back through."""
        if not (system_purpose_str := output.get("stdout", None)):
            return None
        while system_purpose_str:
            try:
                system_purpose_dict = json.loads(system_purpose_str)
                return system_purpose_dict
            except json.decoder.JSONDecodeError as error:
                logger.warning("system_purpose was not valid JSON.  Error: %s", error)
            # We anticipate in some edge cases that unwanted non-JSON outputs may be
            # included in the stdout stream before the actual JSON output, but we expect
            # they are on their own lines. So, chop the first line, try, and repeat.
            # It's a brute-force solution, but this should help in those edge cases!
            if "\n" not in system_purpose_str:
                break
            system_purpose_str = re.sub(r"^.*?\n", "", system_purpose_str)
        return None
