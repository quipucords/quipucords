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


class ProcessJWSInstalledWithRpm(process.Processor):
    """Process the results of 'yum grouplist jws3 jws3plus jws5...'."""

    KEY = 'jws_installed_with_rpm'

    @staticmethod
    def process(output, dependencies=None):
        """Determine if jws was installed with rpm. Version 3 and up."""
        stdout = output.get('stdout_lines', [])
        if len(stdout) == 1 and 'Red Hat JBoss Web Server' in stdout[0]:
            return True
        return False


class ProcessHasJBossEULA(process.Processor):
    """Process result of $(ls $JWS_HOME/JBossEULA.txt)."""

    KEY = 'jws_has_eula_txt_file'

    @staticmethod
    def process(output, dependencies=None):
        """Check if JBossEULA.txt exists in JWS_Home directory."""
        stdout = output.get('stdout_lines', [])
        if len(stdout) == 1 and 'No such file or directory' not in stdout[0]:
            return True
        return False


class ProcessGetVersion(process.Processor):
    """Process output of various searches for version strings."""

    KEY = 'jws_version'

    @staticmethod
    def process(output, dependencies=None):
        """Return array of possible version strings."""
        versions = output.get('results', [])
        results = []

        for version in versions:
            version = version.get('stdout_lines', [])
            if version:
                results.append(version[0])

        return results


class ProcessTomcatPartOfRedhatProduct(process.Processor):
    """Process output of search for redhat string in tomcat files."""

    KEY = 'tomcat_is_part_of_redhat_product'

    @staticmethod
    def process(output, dependencies=None):
        """Return either True or False."""
        result = output.get('stdout_lines', False)
        if result:
            result = result[0]
        if result == 'True':
            return True
        return False
