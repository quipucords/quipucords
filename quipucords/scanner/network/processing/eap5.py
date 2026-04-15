"""Initial processing of raw shell output from Ansible commands."""

import logging
import re

from scanner.network.processing import util

logger = logging.getLogger(__name__)


class ProcessVersionTxt(util.StdoutSearchProcessor):
    """Process the output of 'cat .../version.txt'."""

    KEY = "eap5_home_version_txt"
    SEARCH_STRING = "JBoss Enterprise Application Platform - Version 5"


class ProcessReadmeHtml(util.StdoutSearchProcessor):
    """Process the output of 'cat .../readme.html'."""

    KEY = "eap5_home_readme_html"
    SEARCH_STRING = "JBoss Enterprise Application Platform 5"


class ProcessLsJbossAs(util.IndicatorFileFinder):
    """Process the output of 'ls -1 .../jboss-as'."""

    KEY = "eap5_home_ls_jboss_as"
    INDICATOR_FILES = ["JBossEULA.txt"]


class ProcessRunJarVersion(util.StdoutSearchProcessor):
    """Process the output of 'java -jar run.jar --version'."""

    KEY = "eap5_home_run_jar_version"
    SEARCH_STRING = "JBoss"


class ProcessRunJarManifest(util.PerItemProcessor):
    """Process the MANIFEST.MF file from run.jar."""

    KEY = "eap5_home_run_jar_manifest"

    # Find the line that contains 'Implementation-Version:', then pull
    # out the first non-whitespace token after '(CVS|SVN)Tag=' on that
    # same line.

    VERSION_REGEXP = re.compile(r"Implementation-Version:.*(CVS|SVN)Tag=(\S+)\s*.*")

    @classmethod
    def process_item(cls, item):
        """Look for an EAP version in a MANIFEST.MF file."""
        for line in item["stdout_lines"]:
            match = cls.VERSION_REGEXP.match(line)
            if match:
                return match.group(2)
