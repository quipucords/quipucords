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


# Classifications for the Implementation-Version field of the
# MANIFEST.MF file inside of a run.jar. This dict is from
# https://github.com/mdvickst/ansible-scan-jboss/blob/master/scan-jboss.py
# . According to the project, it is up to date through EAP 6.4 CP04
# and WildFly 10.0.0.CR3.
VERSION_CLASSIFICATIONS = {
    "JBoss_4_0_0": "JBossAS-4",
    "JBoss_4_0_1_SP1": "JBossAS-4",
    "JBoss_4_0_2": "JBossAS-4",
    "JBoss_4_0_3_SP1": "JBossAS-4",
    "JBoss_4_0_4_GA": "JBossAS-4",
    "Branch_4_0": "JBossAS-4",
    "JBoss_4_2_0_GA": "JBossAS-4",
    "JBoss_4_2_1_GA": "JBossAS-4",
    "JBoss_4_2_2_GA": "JBossAS-4",
    "JBoss_4_2_3_GA": "JBossAS-4",
    "JBoss_5_0_0_GA": "JBossAS-5",
    "JBoss_5_0_1_GA": "JBossAS-5",
    "JBoss_5_1_0_GA": "JBossAS-5",
    "JBoss_6.0.0.Final": "JBossAS-6",
    "JBoss_6.1.0.Final": "JBossAS-6",
    "1.0.1.GA": "JBossAS-7",
    "1.0.2.GA": "JBossAS-7",
    "1.1.1.GA": "JBossAS-7",
    "1.2.0.CR1": "JBossAS-7",
    "1.2.0.Final": "WildFly-8",
    "1.2.2.Final": "WildFly-8",
    "1.2.4.Final": "WildFly-8",
    "1.3.0.Beta3": "WildFly-8",
    "1.3.0.Final": "WildFly-8",
    "1.3.3.Final": "WildFly-8",
    "1.3.4.Final": "WildFly-9",
    "1.4.2.Final": "WildFly-9",
    "1.4.3.Final": "WildFly-10",
    "1.4.4.Final": "WildFly-10",
    "JBPAPP_4_2_0_GA": "EAP-4.2",
    "JBPAPP_4_2_0_GA_C": "EAP-4.2",
    "JBPAPP_4_3_0_GA": "EAP-4.3",
    "JBPAPP_4_3_0_GA_C": "EAP-4.3",
    "JBPAPP_5_0_0_GA": "EAP-5.0.0",
    "JBPAPP_5_0_1": "EAP-5.0.1",
    "JBPAPP_5_1_0": "EAP-5.1.0",
    "JBPAPP_5_1_1": "EAP-5.1.1",
    "JBPAPP_5_1_2": "EAP-5.1.2",
    "JBPAPP_5_2_0": "EAP-5.2.0",
    "1.1.2.GA-redhat-1": "EAP-6.0.0",
    "1.1.3.GA-redhat-1": "EAP-6.0.1",
    "1.2.0.Final-redhat-1": "EAP-6.1.0",
    "1.2.2.Final-redhat-1": "EAP-6.1.1",
    "1.3.0.Final-redhat-2": "EAP-6.2",
    "1.3.3.Final-redhat-1": "EAP-6.3",
    "1.3.4.Final-redhat-1": "EAP-6.3",
    "1.3.5.Final-redhat-1": "EAP-6.3",
    "1.3.6.Final-redhat-1": "EAP-6.4",
    "1.3.7.Final-redhat-1": "EAP-6.4",
}


class ProcessRunJarManifest(util.PerItemProcessor):
    """Process the MANIFEST.MF file from run.jar."""

    KEY = "eap5_home_run_jar_manifest"

    # Find the line that contains 'Implementation-Version:', then pull
    # out the first non-whitespace token after '(CVS|SVN)Tag=' on that
    # same line.

    VERSION_REGEXP = re.compile(r"Implementation-Version:.*(CVS|SVN)Tag=(\S+)\s*.*")

    # pylint: disable=inconsistent-return-statements
    @classmethod
    def process_item(cls, item):
        """Look for an EAP version in a MANIFEST.MF file."""
        for line in item["stdout_lines"]:
            match = cls.VERSION_REGEXP.match(line)
            if match:
                return match.group(2)
