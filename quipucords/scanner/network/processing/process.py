"""Infrastructure for the initial data postprocessing."""

import abc
import traceback
from dataclasses import dataclass
from logging import DEBUG, ERROR
from typing import Any

# ### Conventions ####
#
# The processing functions return strings because that's what can fit
# in a RawFact in our database. Normal results are JSON-encoded
# strings. In case of an error, the result is '' and the error is
# logged.

PROCESSORS = {}
NO_DATA = ""  # Result value when we have errors.

DEPS = "DEPS"
REQUIRE_DEPS = "REQUIRE_DEPS"
FAILED = "failed"
KEY = "KEY"
RC = "rc"
RESULTS = "results"
RETURN_CODE_ANY = "RETURN_CODE_ANY"
SKIPPED = "skipped"
STDOUT = "stdout"

QPC_FORCE_POST_PROCESS = "QPC_FORCE_POST_PROCESS"

SUDO_ERROR = "sudo: a password is required"


@dataclass
class ProcessedResult:
    """Processed result including relevant metadata."""

    # return_code == 0 = success
    return_code: int
    error_msg: str = None
    # the actual fact value
    value: Any = None


def is_sudo_error_value(value):
    """Identify values coming from sudo errors.

    The sudo error message can come through even if we use '2>
    /dev/null' in a task. Presumably it's because Ansible wraps our
    entire shell command in something when it runs on the remote
    host. Whatever the reason, we need to handle it in the controller.
    """
    return (
        isinstance(value, str)
        and value == SUDO_ERROR
        or isinstance(value, list)
        and value == [SUDO_ERROR]
        or isinstance(value, dict)
        and value.get(STDOUT, "") == SUDO_ERROR
    )


def is_ansible_task_result(value):
    """Check whether an object is an Ansible task result.

    This function lets us distinguish between standard Ansible results
    that need processing and values that have been postprocessed in
    the playbook.
    """
    return isinstance(value, dict) and (
        SKIPPED in value or FAILED in value or RC in value or RESULTS in value
    )


def process(  # noqa: PLR0911, PLR0912, C901
    scan_task, previous_host_facts, fact_key, fact_value, host
):
    """Do initial processing of the given facts.

    :param scan_task: scan_task for context and logging
    :param previous_host_facts: a dictionary of key, value pairs,
    where values are Ansible result dictionaries.
    :param fact_key: fact key to process
    :param fact_value: unprocessed fact value
    :param host: the host the facts are from. Used for error messages.

    :returns: processed fact value
    """
    # Note: we do NOT support transitive dependencies. If those are
    # needed, this is the place to change.
    if is_sudo_error_value(fact_value):
        log_message = (
            f"POST PROCESSING SUDO ERROR {host}."
            f" fact_key {fact_key} had sudo error {fact_value}"
        )
        scan_task.log_message(log_message, log_level=DEBUG)
        return NO_DATA

    processor = PROCESSORS.get(fact_key)
    if not processor:
        return fact_value

    # Use StopIteration to let the inner for loop continue the
    # outer for loop.
    dependencies = {}
    try:
        require_deps = getattr(processor, REQUIRE_DEPS, True)
        for dep in getattr(processor, DEPS, []):
            if require_deps or isinstance(previous_host_facts.get(dep), Exception):
                if (
                    dep not in previous_host_facts.keys()
                    or not previous_host_facts[dep]
                    or isinstance(previous_host_facts[dep], Exception)
                ):
                    log_message = (
                        f"POST PROCESSING MISSING REQ DEP {host}."
                        f" Fact {fact_key} missing dependency {dep}"
                    )
                    scan_task.log_message(log_message, log_level=DEBUG)
                    raise StopIteration()
            dependencies[dep] = previous_host_facts.get(dep)
    except StopIteration:
        return NO_DATA

    # Don't touch things that are not standard Ansible results,
    # because we don't know what format they will have.
    if fact_value != QPC_FORCE_POST_PROCESS:
        if not is_ansible_task_result(fact_value):
            log_message = (
                f"FAILED POST PROCESSING {host}."
                f" fact_value {fact_key}:{fact_value} needs postprocessing but"
                " is not an Ansible result"
            )
            scan_task.log_message(log_message, log_level=ERROR)
            # We don't know what data is supposed to go here, because
            # we can't run the postprocessor. Leaving the existing
            # data would cause database corruption and maybe trigger
            # other bugs later on. So treat this like any other error.
            return NO_DATA

        if fact_value.get(SKIPPED, False):
            log_message = (
                f"SKIPPED POST PROCESSING {host}."
                f" fact {fact_key} skipped, no results"
            )
            scan_task.log_message(log_message, log_level=DEBUG)
            return NO_DATA

        return_code = fact_value.get(RC, 0)
        if return_code and not getattr(processor, RETURN_CODE_ANY, False):
            log_message = (
                f"FAILED REMOTE COMMAND {host}."
                f" {fact_key} exited with {return_code}: {fact_value['stdout']}"
            )
            scan_task.log_message(log_message, log_level=ERROR)
            return NO_DATA

    try:
        processor_out = processor.process(fact_value, dependencies)
    except Exception:  # noqa: BLE001
        log_message = (
            f"FAILED POST PROCESSING {host}."
            f" Processor for {fact_key} got value {fact_value},"
            f" returned {traceback.format_exc()}"
        )
        scan_task.log_message(log_message, log_level=ERROR)
        return NO_DATA

    return processor_out


class ProcessorMeta(abc.ABCMeta):
    """Metaclass to automatically register Processors."""

    def __init__(cls, name, bases, dct):
        """Register cls in the PROCESSORS dictionary."""
        if "KEY" not in dct:
            raise Exception(f"Processor {name} does not have a KEY")

        # Setting a falsey KEY means "yes, I did this on purpose, I
        # really don't want this class registered."
        if dct[KEY]:
            PROCESSORS[dct[KEY]] = cls
        super().__init__(name, bases, dct)


class Processor(metaclass=ProcessorMeta):
    """A class to process the output of an Ansible task."""

    # Special fields:
    #   KEY: a string. Should match the Ansible fact name that this
    #     will process (required).
    #   DEPS: a list of keys of other facts that this one depends
    #     on. If one of the deps had an error, we will show a "missing
    #     dependency" message rather than an error for this fact
    #     (optional).  If REQUIRE_DEPS is False and a dependency is
    #     missing (not an Exception), processing will continue.
    #   REQUIRE_DEPS: bool indicating whether a missing dependency should
    #      be an error or not.
    #   RETURN_CODE_ANY: if True, process() will pass results with
    #     non-zero return code to this processor. If False, process()
    #     will emit a default error message if the shell command has
    #     non-zero return code (optional, defaults to False).
    #   process(output): a static method. Process the output of the
    #     task (required).

    KEY = None

    @staticmethod
    def process(output, dependencies):
        """Process Ansible output.

        :param output: an Ansible output dictionary. This typically
          has members 'rc', 'stdout', and 'stdout_lines', but may
          instead have a member 'results', which is an array of dicts
          that each have 'rc', 'stdout', 'stdout_lines', and
          'item'.
        :param dependencies: declared dependencies will be passed
          to the processor so values can be examined.

        :returns: a Python object that represents output. Returns
          NO_DATA in case of error.
        """
        raise NotImplementedError()
