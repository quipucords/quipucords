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
from scanner.network.processing import process, util

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

        plain_output = output['stdout'].strip().lower()
        # Yes, id outputs Unicode left and right single quotation
        # marks around the username it doesn't recognize.
        if plain_output == 'id: jboss: no such user' or \
           plain_output == 'id: ‘jboss’: no such user':
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

    IGNORE_PROCESSES = ['bash', 'grep', 'oom_reaper']

    @staticmethod
    def process(output):
        """Return the number of jboss eap processes on the system."""
        # The task on the remote host requires three processes: a ps,
        # a grep, and a bash to run the pipeline. Of those, the bash
        # and the grep will both match the pattern we are searching
        # for. However, there is a race condition - sometimes the ps
        # starts and grabs the process table before the grep is in it,
        # and sometimes not.
        num_matches = 0
        for line in output['stdout_lines']:
            parts = line.split(None, 1)
            if parts[0] in ProcessJbossEapProcesses.IGNORE_PROCESSES:
                continue
            num_matches += 1

        return num_matches


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


class ProcessJbossEapChkconfig(util.InitLineFinder):
    """Process the output of 'chkconfig'."""

    DEPS = ['have_chkconfig']
    KEY = 'jboss_eap_chkconfig'
    KEYWORDS = ['jboss', 'eap']


class ProcessJbossEapSystemctl(util.InitLineFinder):
    """Process the output of 'systemctl list-unit-files'."""

    DEPS = ['have_systemctl']
    KEY = 'jboss_eap_systemctl_unit_files'
    KEYWORDS = ['jboss', 'eap']


class ProcessEapHomeLs(util.IndicatorFileFinder):
    """Process the output of 'ls -1 ...'."""

    KEY = 'eap_home_ls'

    INDICATOR_FILES = ['appclient', 'standalone', 'JBossEULA.txt',
                       'modules', 'jboss-modules.jar', 'version.txt']


class ProcessEapHomeVersionTxt(util.StdoutPassthroughProcessor):
    """Process the output of 'cat .../version.txt'."""

    KEY = 'eap_home_version_txt'


class ProcessEapHomeReadmeTxt(util.StdoutSearchProcessor):
    """Process the output of 'cat .../README.txt'."""

    KEY = 'eap_home_readme_txt'
    SEARCH_STRING = 'Welcome to WildFly'


class ProcessJbossModulesManifestMf(util.StdoutPassthroughProcessor):
    """Process the jboss-modules.jar MANIFEST.MF file's contents."""

    KEY = 'eap_home_jboss_modules_manifest'


class ProcessJbossModulesVersion(util.StdoutPassthroughProcessor):
    """Process the output of 'java -jar jboss-modules.jar -version'."""

    KEY = 'eap_home_jboss_modules_version'


class ProcessEapHomeBinForFuse(util.IndicatorFileFinder):
    """Process the output of 'ls -1' for eap_home_bin to check for fuse."""

    KEY = 'eap_home_bin'

    INDICATOR_FILES = ['fuseconfig.sh', 'fusepatch.sh']


class ProcessEapHomeLayers(process.Processor):
    """Process the output of eap home layers."""

    KEY = 'eap_home_layers'

    @staticmethod
    def process(output):
        """Pass the output back through."""
        return {result['item']: result['rc'] == 0
                for result in output['results']}


class ProcessEapHomeLayersConf(process.Processor):
    """Process the output of eap home layers conf."""

    KEY = 'eap_home_layers_conf'

    @staticmethod
    def process(output):
        """Pass the output back through."""
        return {result['item']: result['rc'] == 0
                for result in output['results']}


class ProcessFindJbossEAPJarVer(util.FindJarVer):
    """Process the results of a find jar version command."""

    KEY = 'jboss_eap_jar_ver'


class ProcessFindJbossEAPRunJarVer(util.FindJarVer):
    """Process the results of a find jar version command."""

    KEY = 'jboss_eap_run_jar_ver'
