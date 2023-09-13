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
        """
        Get the DMI system UUID from output if present.

        Get only the last "valid" value from the stdout lines (where "valid" just means
        it has length <= 36). This seems really lazy and problematic, and we should
        FIXME this "UUID validation" at some point.

        Note that we are processing the stdout lines in reverse order because a badly
        configured target system may inject unexpected lines at the start of stdout.
        """
        dmi_system_uuid = dependencies.get("internal_dmi_system_uuid")
        if dmi_system_uuid and dmi_system_uuid.get("rc") == 0:
            stdout_lines = dmi_system_uuid.get("stdout_lines", [])
            for dmi_system_uuid in stdout_lines[::-1]:
                if 0 < len(dmi_system_uuid) <= 36:  # noqa: PLR2004
                    return dmi_system_uuid
                logger.warning(
                    "dmi_system_uuid is invalid because "
                    "its length is greater than 36.  "
                    "dmi_system_uuid value: %s",
                    dmi_system_uuid,
                )
        return ""
