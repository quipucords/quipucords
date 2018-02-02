# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Infrastructure for the initial data postprocessing."""

import abc
import json
import logging
import traceback

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# ### Conventions ####
#
# The processing functions return strings because that's what can fit
# in a RawFact in our database. Normal results are JSON-encoded
# strings. In case of an error, the result is '' and the error is
# logged.

PROCESSORS = {}
NO_DATA = ''  # Result value when we have errors.

DEPS = 'DEPS'
FAILED = 'failed'
KEY = 'KEY'
RC = 'rc'
RESULTS = 'results'
RETURN_CODE_ANY = 'RETURN_CODE_ANY'
SKIPPED = 'skipped'


def is_ansible_task_result(value):
    """Check whether an object is an Ansible task result.

    This function lets us distinguish between standard Ansible results
    that need processing and values that have been postprocessed in
    the playbook.
    """
    return (isinstance(value, dict) and
            (SKIPPED in value or
             FAILED in value or
             RC in value or
             RESULTS in value))


def process(facts, host):
    """Do initial processing of the given facts.

    :param facts: a dictionary of key, value pairs, where values are
      Ansible result dictionaries.
    :param host: the host the facts are from. Used for error messages.

    :returns: a dictionary of key, value pairs, where the values are
      strings. They will either be JSON-encoded data, or the empty
      string on errors.
    """
    result = facts.copy()

    # Note: we do NOT support transitive dependencies. If those are
    # needed, this is the place to change.
    for key, value in facts.items():
        processor = PROCESSORS.get(key)
        if not processor:
            continue

        # Use StopIteration to let the inner for loop continue the
        # outer for loop.
        try:
            for dep in getattr(processor, DEPS, []):
                if dep not in facts or \
                   not facts[dep] or \
                   isinstance(facts[dep], Exception):
                    logger.debug('%s: fact %s missing dependency %s',
                                 host, key, dep)
                    result[key] = NO_DATA
                    raise StopIteration()
        except StopIteration:
            continue

        # Don't touch things that are not standard Ansible results,
        # because we don't know what format they will have.
        if not is_ansible_task_result(value):
            logger.error('%s: value %s:%s needs postprocessing but is not an '
                         'Ansible result', host, key, value)
            # We don't know what data is supposed to go here, because
            # we can't run the postprocessor. Leaving the existing
            # data would cause database corruption and maybe trigger
            # other bugs later on. So treat this like any other error.
            result[key] = NO_DATA
            continue

        if value.get(SKIPPED, False):
            logger.debug('%s: fact %s skipped, no results', host, key)
            result[key] = NO_DATA
            continue

        return_code = value.get(RC, 0)
        if return_code and not getattr(processor, RETURN_CODE_ANY, False):
            logger.error('%s: remote command for %s exited with %s: %s',
                         host, key, return_code, value['stdout'])
            result[key] = NO_DATA
            continue

        try:
            processor_out = processor.process(value)
        except Exception:  # pylint: disable=broad-except
            logger.error('%s: processor for %s got value %s, returned %s',
                         host, key, value, traceback.format_exc())
            result[key] = NO_DATA
            continue

        # https://docs.python.org/3/library/json.html suggests that
        # these separators will give the most compact representation.
        result[key] = json.dumps(processor_out, separators=(',', ':'))

    return result


class ProcessorMeta(abc.ABCMeta):
    """Metaclass to automatically register Processors."""

    def __init__(cls, name, bases, dct):
        """Register cls in the PROCESSORS dictionary."""
        if 'KEY' not in dct:
            raise Exception('Processor {0} does not have a KEY'.format(name))

        # Setting a falsey KEY means "yes, I did this on purpose, I
        # really don't want this class registered."
        if dct[KEY]:
            PROCESSORS[dct[KEY]] = cls
        super().__init__(name, bases, dct)


# pylint: disable=too-few-public-methods
class Processor(object, metaclass=ProcessorMeta):
    """A class to process the output of an Ansible task."""

    # Special fields:
    #   KEY: a string. Should match the Ansible fact name that this
    #     will process (required).
    #   DEPS: a list of keys of other facts that this one depends
    #     on. If one of the deps had an error, we will show a "missing
    #     dependency" message rather than an error for this fact
    #     (optional).
    #   RETURN_CODE_ANY: if True, process() will pass results with
    #     non-zero return code to this processor. If False, process()
    #     will emit a default error message if the shell command has
    #     non-zero return code (optional, defaults to False).
    #   process(output): a static method. Process the output of the
    #     task (required).

    KEY = None

    @staticmethod
    def process(output):
        """Process Ansible output.

        :param output: an Ansible output dictionary. This typically
          has members 'rc', 'stdout', and 'stdout_lines', but may
          instead have a member 'results', which is an array of dicts
          that each have 'rc', 'stdout', 'stdout_lines', and
          'item'.

        :returns: a Python object that represents output. Returns
          NO_DATA in case of error.
        """
        raise NotImplementedError()
