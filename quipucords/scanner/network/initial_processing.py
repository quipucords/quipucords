# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Initial processing of raw shell output from Ansible commands."""

import abc
import json

# ### Conventions ####
#
# The processing functions return strings because that's what can fit
# in a RawFact in our database. To keep things understandable,
#   - All error strings start with 'Error:'
#   - Everything else is JSON-encoded

# #### Infrastructure ####

PROCESSORS = {}


def process(facts):
    """Do initial processing of the given facts.

    :param facts: a dictionary of key, value pairs, where values are
      Ansible result dictionaries.

    :returns: a dictionary of key, value pairs, where the values are
      strings.
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
                    result[key] = 'Error: {0} missing dependency {1}'.format(
                        key, dep)
                    raise StopIteration()
        except StopIteration:
            continue

        if value.get('skipped', False):
            result[key] = 'Error: {0} skipped, no results'.format(key)
            continue

        if value.get('rc', 0) and \
           not getattr(processor, 'RETURN_CODE_ANY', False):
            result[key] = 'Error: remote command returned {0}'.format(
                value['stdout'])
            continue

        try:
            processor_out = processor.process(value)
        except Exception as ex:  # pylint: disable=broad-except
            result[key] = 'Error: processor returned {0}'.format(str(ex))
            continue

        if isinstance(processor_out, Exception):
            result[key] = 'Error: {0}'.format(' '.join(processor_out.args))
            continue

        result[key] = json.dumps(processor_out,
                                 indent=' ', separators=(',', ':'))

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

        :returns: a Python object that represents output. Will return
          an instance of Exception if it can't find the expected
          information.
        """
        raise NotImplementedError()


# #### Processors ####

FIND_WARNING = 'find: WARNING: Hard link count is wrong for /proc: this may' \
               ' be a bug in your filesystem driver.'


class ProcessJbossEapRunningPaths(Processor):
    """Process a list of JBoss EAP processes."""

    KEY = 'internal_jboss_eap_running_paths'

    DEPS = ['internal_have_java']

    @staticmethod
    def process(output):
        """Just preserve the output, except for a known issue."""
        if FIND_WARNING in output['stdout']:
            return ValueError('find command failed')
        return output['stdout'].strip()


class ProcessFindJboss(Processor):
    """Process the results of a find command."""

    KEY = 'internal_jboss_eap_find_jboss_modules_jar'

    @staticmethod
    def process(output):
        """Return the command's output."""
        return output['stdout_lines']


class ProcessIdUJboss(Processor):
    """Process the results of 'id -u jboss'."""

    KEY = 'internal_jboss_eap_id_jboss'

    RETURN_CODE_ANY = True

    @staticmethod
    def process(output):
        """Check whether id succeeded or failed."""
        if output['rc'] == 0:
            return True

        plain_output = output['stdout'].strip()
        if plain_output.lower() == 'id: jboss: no such user':
            return False

        return ValueError('unexpected output {0}'.format(plain_output))


class ProcessJbossEapCommonFiles(Processor):
    """Process the output of 'test -e ...'."""

    KEY = 'jboss_eap_common_files'

    @staticmethod
    def process(output):
        """Find all of the times 'test' succeeded."""
        items = output['results']

        out_list = []
        for item in items:
            directory = item['item']
            if 'rc' in item and item['rc'] == 0:
                out_list.append(directory)

            # If 'rc' is in item but is nonzero, the directory wasn't
            # present. If 'rc' isn't in item, there was an error and the
            # test wasn't run.

        return out_list


class ProcessJbossEapProcesses(Processor):
    """Process the output of a process search."""

    KEY = 'jboss_eap_processes'

    @staticmethod
    def process(output):
        """Return the number of jboss eap processes on the system."""
        # pgrep exists with status 0 if it finds processes matching its
        # pattern, and status 1 if not.
        if output['rc']:
            return 0

        # There should always be two processes matching 'eap', one for
        # the grep that's searching for 'eap', and one for the bash
        # that's running the pipeline.
        num_procs = len(output['stdout_lines'])

        if num_procs < 2:
            return 'Error: bad result ({0} processes)'.format(num_procs)

        return num_procs - 2


class ProcessJbossEapPackages(Processor):
    """Process the output of an rpm query."""

    KEY = 'jboss_eap_packages'

    @staticmethod
    def process(output):
        """Count the number of lines of output."""
        if output['rc']:
            return 'Error: pipeline returned non-zero status'

        return len(output['stdout_lines'])


class ProcessJbossEapLocate(Processor):
    """Process the output of 'locate jboss-modules.jar'."""

    KEY = 'jboss_eap_locate_jboss_modules_jar'

    @staticmethod
    def process(output):
        """Pass the output back through."""
        if not output['rc']:
            return output['stdout_lines']

        return ValueError('locate returned non-zero status')


class InitLineFinder(Processor):
    """Process the output of an init system.

    For both chkconfig and systemctl list-unit-files, we look for
    lines where the first (whitespace-delineated) element contains
    'jboss' or 'eap'.
    """

    KEY = None

    @staticmethod
    def process(output):
        """Find lines where the first element contains 'jboss' or 'eap'."""
        matches = []

        for line in output['stdout_lines']:
            if not line:
                continue

            start = line.split()[0]
            if 'jboss' in start or 'eap' in start:
                matches.append(line.strip())

        return matches


class ProcessJbossEapChkconfig(InitLineFinder):
    """Process the output of 'chkconfig'."""

    KEY = 'jboss_eap_chkconfig'


class ProcessJbossEapSystemctl(InitLineFinder):
    """Process the output of 'systemctl list-unit-files'."""

    KEY = 'jboss_eap_systemctl_unit_files'


class IndicatorFileFinder(Processor):
    """Look for indicator files in the output of many 'ls -1's.

    Use by subclassing and defining a class variable INDICATOR_FILES,
    which is an iterable of the files to look for. Example usage:

    class ProcessMyLsResults(IndicatorFileFinder):
        KEY = 'my_great_ls'
        INDICATOR_FILES = ['find', 'my', 'directory']
    """

    KEY = None

    @classmethod
    def process(cls, output):
        """Find indicator files in the output, item by item."""
        results = {}

        for item in output['results']:
            directory = item['item']
            if item['rc']:
                results[directory] = ''
                continue

            files = item['stdout_lines']
            # pylint: disable=no-member
            found_in_dir = [filename for filename in cls.INDICATOR_FILES
                            if filename in files]
            if found_in_dir:
                results[directory] = found_in_dir
            else:
                results[directory] = []

        return results


class CatResultsProcessor(Processor):
    """Look for 'Red Hat' in the output of many 'cat's.

    Use by making subclasses with their own KEYs.
    """

    KEY = None

    @staticmethod
    def process(output):
        """Process the output of a with_items cat from Ansible.

        :param cat_out: the output of a with_items cat task from
        Ansible.

        :returns: a dictionary mapping each directory name to True if
          'Red Hat' was found in that directory's cat, and False
          otherwise.
        """
        results = {}
        for item in output['results']:
            directory = item['item']
            if item['rc']:
                results[directory] = False
            else:
                results[directory] = 'Red Hat' in item['stdout']

        return results


class ProcessEapHomeLs(IndicatorFileFinder):
    """Process the output of 'ls -1 ...'."""

    KEY = 'ls_eap_home'

    INDICATOR_FILES = ['appclient', 'standalone', 'JBossEULA.txt',
                       'modules', 'jboss-modules.jar', 'version.txt']


class ProcessEapHomeCat(CatResultsProcessor):
    """Process the output of 'cat .../version.txt'."""

    KEY = 'eap_home_version_txt'
