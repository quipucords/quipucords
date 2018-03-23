# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Initial processing of the shell output from the jboss_brms role."""

import logging
from scanner.network.processing import process, util

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# pylint: disable=too-few-public-methods

# #### Processors ####


class ProcessJbossBRMSManifestMF(util.PerItemProcessor):
    """Process the MANIFEST.MF files."""

    KEY = 'jboss_brms_manifest_mf'

    @staticmethod
    def process_item(item):
        """Return stdout if not empty."""
        return item['stdout'] or None


class ProcessJbossBRMSKieBusinessCentral(process.Processor):
    """Process ls results for kie-api files."""

    KEY = 'jboss_brms_kie_in_business_central'

    @staticmethod
    def process(output):
        """Return the command's output."""
        kie_api_files = []
        for result in output['results']:
            if 'rc' in result and result['rc'] == 0:
                kie_api_files.extend(result['stdout_lines'])
        return kie_api_files


class ProcessFindBRMSKieApiVer(process.Processor):
    """Process the results of a find command."""

    KEY = 'jboss_brms_kie_api_ver'

    @staticmethod
    def process(output):
        """Return the command's output."""
        return output['stdout_lines']


class ProcessFindBRMSDroolsCoreVer(process.Processor):
    """Process the results of a find command."""

    KEY = 'jboss_brms_drools_core_ver'

    @staticmethod
    def process(output):
        """Return the command's output."""
        return output['stdout_lines']


class ProcessFindBRMSKieWarVer(process.Processor):
    """Process the results of a find command."""

    KEY = 'jboss_brms_kie_war_ver'

    @staticmethod
    def process(output):
        """Return the command's output."""
        return output['stdout_lines']
