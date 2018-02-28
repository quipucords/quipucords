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
from scanner.network.processing import util

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# pylint: disable=too-few-public-methods


class ProcessVersionTxt(util.StdoutSearchProcessor):
    """Process the output of 'cat .../version.txt'."""

    KEY = 'eap5_home_version_txt'
    SEARCH_STRING = 'JBoss Enterprise Application Platform'


class ProcessReadmeHtml(util.StdoutSearchProcessor):
    """Process the output of 'cat .../readme.html'."""

    KEY = 'eap5_home_readme_html'
    SEARCH_STRING = 'JBoss Enterprise Application Platform'


class ProcessLsJbossAs(util.IndicatorFileFinder):
    """Process the output of 'ls -1 .../jboss-as'."""

    KEY = 'eap5_home_ls_jboss_as'
    INDICATOR_FILES = ['JBossEULA.txt']


class ProcessRunJarVersion(util.StdoutSearchProcessor):
    """Process the output of 'java -jar run.jar --version'."""

    KEY = 'eap5_home_run_jar_version'
    SEARCH_STRING = 'JBoss'
