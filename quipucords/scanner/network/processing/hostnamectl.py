"""Initial processing of the shell output from the hostnamectl role."""

import logging

from scanner.network.processing.process import RC, ProcessedResult, Processor

logger = logging.getLogger(__name__)


class ProcessHostnameCTL(Processor):
    """Process the hostnamectl fact."""

    KEY = "hostnamectl"

    @staticmethod
    def process(output, dependencies=None):
        """Process hostnamectl fact output."""
        return ProcessHostnameCTL._process(output)

    @classmethod
    def _process(cls, output, dependencies=None):
        """
        Process hostnamectl fact output.

        Note that this function assumes `hostnamectl status` is called with no
        additional arguments. Although the `--json` argument could make output
        more consistent and simplify this function, that argument is not
        widely available enough for our needs at the time of this writing.
        """
        if output.get(RC) != 0:
            return cls._handle_non_zero_rc(output)
        hostnamectl_facts = {}
        # Note: we have reference example outputs in testdata/hostnamectl-status.
        stdout_lines: list[str] = output.get("stdout_lines")
        for line in stdout_lines:
            if ":" not in line:
                continue
            fact_name, fact_value = line.split(":", 1)
            fact_name = fact_name.strip().lower().replace(" ", "_")
            if fact_name == "chassis":
                # The documented values for chassis value are single words
                # but the value is often accompanied by an emoji like "vm 🖴"
                fact_value = fact_value.split()[0]
            hostnamectl_facts[fact_name] = fact_value.strip()
        return ProcessedResult(return_code=0, value=hostnamectl_facts)

    @classmethod
    def _handle_non_zero_rc(cls, output):
        return_code = output.get(RC)
        stderr = output.get("stderr")
        stdout = output.get("stdout")
        logger.warning(
            "unable to process hostnamectl due to error in fact collection\n"
            f"{return_code=}\n"
            f"{stderr=}\n"
            f"{stdout=}\n"
            "---"
        )
        if stderr:
            error_msg = stderr
        if stdout:
            error_msg = (
                f"unexpected return code ({return_code}) for 'hostnamectl status'. "
                f"Full output from command:\n{stdout}"
            )

        return ProcessedResult(return_code=return_code, error_msg=error_msg)
