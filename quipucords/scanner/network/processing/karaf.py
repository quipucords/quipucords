# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Initial processing of the shell output from the jboss_fuse_on_karaf role."""

import logging
from scanner.network.processing import process

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# pylint: disable=too-few-public-methods

# #### Processors ####

FIND_WARNING = 'find: WARNING: Hard link count is wrong for /proc: this may' \
               ' be a bug in your filesystem driver.'


class ProcessKarafRunningProcesses(process.Processor):
    """Process a list of Jboss Fuse on Karaf processes."""

    KEY = 'karaf_running_processes'

    @staticmethod
    def process(output):
        """Preserve the output except for a known issue."""
        if FIND_WARNING in output['stdout']:
            logging.error('Find command failed')
            return process.NO_DATA

        return output['stdout'].strip()


class ProcessFindKaraf(process.Processor):
    """Process the results of a find command."""

    KEY = 'karaf_find_karaf_jar'

    @staticmethod
    def process(output):
        """Return the command's output."""
        print('\n\n\nProcessFindKaraf )line 50): \n')
        print(str(output['stdout_lines']))
        return output['stdout_lines']


class ProcessLocateKaraf(process.Processor):
    """Process the output of 'locate jboss.fuse-on-karaf.karaf-home'."""

    KEY = 'karaf_locate_karaf_jar'

    DEPS = ['have_locate']

    @staticmethod
    def process(output):
        """Pass the output back through."""
        return output['stdout_lines']


class InitLineFinder(process.Processor):
    """Process the output of an init system.

    For both chkconfig and systemctl list-unit-files, we look for
    lines where the first (whitespace-delineated) element contains
    'jboss' or 'fuse'.
    """

    # This same code is in eap but I wasn't sure how to make the keyword an
    # argument since it is in a class (without doing an __init__)
    KEY = None

    @staticmethod
    def process(output):
        """Find lines where the first element contains 'jboss' or 'fuse'."""
        matches = []

        for line in output['stdout_lines']:
            if not line:
                continue

            start = line.split()[0]
            if 'jboss' in start or 'fuse' in start:
                matches.append(line.strip())

        return matches


class ProcessJbossFuseChkconfig(InitLineFinder):
    """Process the output of 'chkconfig'."""

    KEY = 'jboss_fuse_chkconfig'


class ProcessJbossFuseSystemctl(InitLineFinder):
    """Process the output of 'systemctl list-unit-files'."""

    KEY = 'jboss_fuse_systemctl_unit_files'


class ProcessKarafHomeBinFuse(process.Processor):
    """Process karaf home indicators to detect Fuse-on-Karaf."""

    KEY = 'karaf_home_bin_fuse'

    @staticmethod
    def process(output):
        """Pass the output back through."""
        return output['stdout_lines']
