# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Initial processing of raw shell output from Ansible commands."""

import logging
from scanner.network.processing import process

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# pylint: disable=too-few-public-methods

# #### Processors ####

FIND_WARNING = 'find: WARNING: Hard link count is wrong for /proc: this may' \
               ' be a bug in your filesystem driver.'


class ProcessJbossEapRunningPaths(process.Processor):
    """Process a list of JBoss EAP processes."""

    KEY = 'jboss_eap_running_paths'

    DEPS = ['have_java']

    @staticmethod
    def process(output):
        """Just preserve the output, except for a known issue."""
        if FIND_WARNING in output['stdout']:
            logger.error('Find command failed')
            return process.NO_DATA

        return output['stdout'].strip()


class ProcessFindJboss(process.Processor):
    """Process the results of a find command."""

    KEY = 'jboss_eap_find_jboss_modules_jar'

    @staticmethod
    def process(output):
        """Return the command's output."""
        return output['stdout_lines']


class ProcessIdUJboss(process.Processor):
    """Process the results of 'id -u jboss'."""

    KEY = 'jboss_eap_id_jboss'

    RETURN_CODE_ANY = True

    @staticmethod
    def process(output):
        """Check whether id succeeded or failed."""
        if output['rc'] == 0:
            return True

        plain_output = output['stdout'].strip()
        if plain_output.lower() == 'id: jboss: no such user':
            return False

        logger.error('id: unexpected output %s', plain_output)
        return process.NO_DATA


class ProcessJbossEapCommonFiles(process.Processor):
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


class ProcessJbossEapProcesses(process.Processor):
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
            logger.error('Bad result from ps (%s processes)', num_procs)
            return process.NO_DATA

        return num_procs - 2


class ProcessJbossEapPackages(process.Processor):
    """Process the output of an rpm query."""

    KEY = 'jboss_eap_packages'

    @staticmethod
    def process(output):
        """Count the number of lines of output."""
        return len(output['stdout_lines'])


class ProcessJbossEapLocate(process.Processor):
    """Process the output of 'locate jboss-modules.jar'."""

    KEY = 'jboss_eap_locate_jboss_modules_jar'

    DEPS = ['have_locate']

    @staticmethod
    def process(output):
        """Pass the output back through."""
        return output['stdout_lines']


class InitLineFinder(process.Processor):
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


class IndicatorFileFinder(process.Processor):
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
                results[directory] = []
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


class CatResultsProcessor(process.Processor):
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
