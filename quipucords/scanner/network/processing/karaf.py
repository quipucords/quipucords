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

from scanner.network.processing import process, util

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
        return output['stdout_lines']


class ProcessLocateKaraf(process.Processor):
    """Process the output of 'locate jboss.fuse-on-karaf.karaf-home'."""

    KEY = 'karaf_locate_karaf_jar'

    DEPS = ['have_locate']

    @staticmethod
    def process(output):
        """Pass the output back through."""
        return output['stdout_lines']


class ProcessJbossFuseChkconfig(util.InitLineFinder):
    """Process the output of 'chkconfig'."""

    DEPS = ['have_chkconfig']
    KEY = 'jboss_fuse_chkconfig'
    KEYWORDS = ['fuse']


class ProcessJbossFuseSystemctl(util.InitLineFinder):
    """Process the output of 'systemctl list-unit-files'."""

    DEPS = ['have_systemctl']
    KEY = 'jboss_fuse_systemctl_unit_files'
    KEYWORDS = ['fuse']
    IGNORE_WORDS = ['sys-fs-fuse-connections.mount']


class ProcessKarafHomeBinFuse(process.Processor):
    """Process karaf home indicators to detect Fuse-on-Karaf."""

    KEY = 'karaf_home_bin_fuse'

    @staticmethod
    def process(output):
        """Pass the output back through."""
        return {result['item']: result['rc'] == 0
                for result in output['results']}


class ProcessKarafHomeSystemOrgJboss(process.Processor):
    """Process the karaf_home_system_org_jboss fact."""

    KEY = 'karaf_home_system_org_jboss'

    @staticmethod
    def process(output):
        """Pass the output back through."""
        return {str(result['stdout_lines']): result['rc'] == 0
                for result in output['results']}


class FuseVersionProcessor(process.Processor):
    """Pass the item name and std out to the fingerprinter.

    Used for with_items tasks when looking for fuse version
    """

    KEY = None

    @staticmethod
    def process(output):
        """Process the output of a with_items task from Ansible.

        :param output: the output of a with_items task.

        :returns: a list containing dictionaries defining the home
        directory and version, or an empty list
        """
        results = []
        for item in output['results']:
            result = {}
            item_name = item['item']
            if item['rc']:
                pass
            else:
                if item['stdout'] != '':
                    value = str(item['stdout']).splitlines()
                    result['install_home'] = item_name
                    result['version'] = list(set(value))
            if result:
                results.append(result)
        return results


class FuseVersionProcessorLocate(process.Processor):
    """Pass stdout lines to the fingerprinter.

    Used for locate tasks when looking for fuse version
    """

    KEY = None

    @staticmethod
    def process(output):
        """Process the output of a with_items task from Ansible.

        :param output: the output of a with_items task.

        :returns: a list containing the version or an empty list
        """
        results = []
        if not output['rc']:
            results = list(set(output['stdout_lines']))
        return results


class ProcessJbossFuseCamelVersion(FuseVersionProcessor):
    """Process the output of looking for camel version'."""

    KEY = 'jboss_fuse_on_karaf_camel_ver'


class ProcessJbossFuseActivemqVersion(FuseVersionProcessor):
    """Process the output of looking for activemq version'."""

    KEY = 'jboss_fuse_on_karaf_activemq_ver'


class ProcessJbossFuseCxfVersion(FuseVersionProcessor):
    """Process the output of looking for cxf version'."""

    KEY = 'jboss_fuse_on_karaf_cxf_ver'


class ProcessJbossFuseOnEapCamelVersion(FuseVersionProcessor):
    """Process the output of looking for camel version'."""

    KEY = 'jboss_fuse_on_eap_camel_ver'


class ProcessJbossFuseOnEapActivemqVersion(FuseVersionProcessor):
    """Process the output of looking for activemq version'."""

    KEY = 'jboss_fuse_on_eap_activemq_ver'


class ProcessJbossFuseOnEapCxfVersion(FuseVersionProcessor):
    """Process the output of looking for cxf version'."""

    KEY = 'jboss_fuse_on_eap_cxf_ver'


class ProcessLocateCamel(FuseVersionProcessorLocate):
    """Process the output of 'locate camel-core'."""

    KEY = 'jboss_fuse_camel_ver'
    DEPS = ['have_locate']


class ProcessLocateActivemq(FuseVersionProcessorLocate):
    """Process the output of 'locate activemq'."""

    KEY = 'jboss_fuse_activemq_ver'
    DEPS = ['have_locate']


class ProcessLocateCxf(FuseVersionProcessorLocate):
    """Process the output of 'locate cxf-rt'."""

    KEY = 'jboss_fuse_cxf_ver'
    DEPS = ['have_locate']
