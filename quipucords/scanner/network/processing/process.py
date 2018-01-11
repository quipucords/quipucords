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

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# ### Conventions ####
#
# The processing functions return strings because that's what can fit
# in a RawFact in our database. Normal results are JSON-encoded
# strings. In case of an error, the result is '' and the error is
# logged.

PROCESSORS = {}
NO_DATA = ''  # Result value when we have errors.


def process(facts):
    """Do initial processing of the given facts.

    :param facts: a dictionary of key, value pairs, where values are
      Ansible result dictionaries.

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
            for dep in getattr(processor, 'DEPS', []):
                if dep not in facts or \
                   not facts[dep] or \
                   isinstance(facts[dep], Exception):
                    logger.error('Fact %s missing dependency %s',
                                 key, dep)
                    result[key] = NO_DATA
                    raise StopIteration()
        except StopIteration:
            continue

        if value.get('skipped', False):
            logger.error('Fact %s skipped, no results', key)
            result[key] = NO_DATA
            continue

        if value.get('rc', 0) and \
           not getattr(processor, 'RETURN_CODE_ANY', False):
            logger.error('Remote command returned %s', value['stdout'])
            result[key] = NO_DATA
            continue

        try:
            processor_out = processor.process(value)
        except Exception as ex:  # pylint: disable=broad-except
            logger.error('Processor returned %s', str(ex))
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
        if dct['KEY']:
            PROCESSORS[dct['KEY']] = cls
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
