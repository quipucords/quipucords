"""Initial processing of the shell output from the dmi role."""
import logging

from scanner.network.processing import process

logger = logging.getLogger(__name__)


class ProcessDmiSystemUuid(process.Processor):
    """Process the dmi system uuid."""

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
                if result[0] == "" and len(result) > 1:  # noqa: PLC1901
                    dmi_system_uuid = result[1]
                if len(dmi_system_uuid) <= 36:  # noqa: PLR2004
                    return dmi_system_uuid
                logger.warning(
                    "dmi_system_uuid is invalid because "
                    "its length is greater than 36.  "
                    "dmi_system_uuid value: %s",
                    dmi_system_uuid,
                )
        return ""
