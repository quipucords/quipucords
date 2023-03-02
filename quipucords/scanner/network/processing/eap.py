"""Initial processing of raw shell output from Ansible commands."""

import logging
import re

from scanner.network.processing import process, util

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# pylint: disable=too-few-public-methods

# #### Processors ####

FIND_WARNING = (
    "find: WARNING: Hard link count is wrong for /proc: this may"
    " be a bug in your filesystem driver."
)


class ProcessJbossEapRunningPaths(process.Processor):
    """Process a list of JBoss EAP processes."""

    KEY = "jboss_eap_running_paths"

    DEPS = ["internal_have_java"]

    @staticmethod
    def process(output, dependencies=None):
        """Just preserve the output, except for a known issue."""
        if FIND_WARNING in output["stdout"]:
            logger.error("Find command failed")
            return process.NO_DATA
        result = [path.strip() for path in output["stdout_lines"] if path]

        return result


class ProcessFindJboss(process.Processor):
    """Process the results of a find command."""

    KEY = "jboss_eap_find_jboss_modules_jar"

    @staticmethod
    def process(output, dependencies=None):
        """Return the command's output."""
        result = [line for line in output.get("stdout_lines", []) if line.split()]
        return result


class ProcessIdUJboss(process.Processor):
    """Process the results of 'id -u jboss'."""

    KEY = "jboss_eap_id_jboss"

    RETURN_CODE_ANY = True

    @staticmethod
    def process(output, dependencies=None):
        """Check whether id succeeded or failed."""
        if output.get("rc", 1) == 0:
            return True

        plain_output = output["stdout"].strip().lower()
        # Yes, id outputs Unicode left and right single quotation
        # marks around the username it doesn't recognize.
        if plain_output in ["id: jboss: no such user", "id: ‘jboss’: no such user"]:
            return False

        logger.error("id: unexpected output %s", plain_output)
        return process.NO_DATA


class ProcessJbossEapCommonFiles(process.Processor):
    """Process the output of 'test -e ...'."""

    KEY = "jboss_eap_common_files"

    @staticmethod
    def process(output, dependencies=None):
        """Find all of the times 'test' succeeded."""
        items = output.get("results", [])

        out_list = []
        for item in items:
            directory = item["item"]
            if "rc" in item and item["rc"] == 0:
                out_list.append(directory)

            # If 'rc' is in item but is nonzero, the directory wasn't
            # present. If 'rc' isn't in item, there was an error and the
            # test wasn't run.

        return out_list


class ProcessJbossProcesses(process.Processor):
    """Process the output of a process search."""

    KEY = "jboss_processes"

    RETURN_CODE_ANY = True

    IGNORE_PROCESSES = ["bash", "grep", "oom_reaper"]

    @staticmethod
    def process(output, dependencies=None):
        """Return the number of jboss eap processes on the system."""
        # The task on the remote host requires three processes: a ps,
        # a grep, and a bash to run the pipeline. Of those, the bash
        # and the grep will both match the pattern we are searching
        # for. However, there is a race condition - sometimes the ps
        # starts and grabs the process table before the grep is in it,
        # and sometimes not.
        num_matches = 0

        if output.get("rc", 1) != 0:
            return num_matches

        for line in output["stdout_lines"]:
            parts = line.split(None, 1)
            if parts[0] in ProcessJbossProcesses.IGNORE_PROCESSES:
                continue
            num_matches += 1

        return num_matches


class ProcessJbossEapPackages(process.Processor):
    """Process the output of an rpm query."""

    KEY = "jboss_eap_packages"

    @staticmethod
    def process(output, dependencies=None):
        """Count the number of lines of output."""
        return len(output["stdout_lines"])


class ProcessJbossEapLocate(process.Processor):
    """Process the output of 'locate jboss-modules.jar'."""

    KEY = "jboss_eap_locate_jboss_modules_jar"

    DEPS = ["internal_have_locate"]

    @staticmethod
    def process(output, dependencies=None):
        """Pass the output back through."""
        result = [path.strip() for path in output["stdout_lines"] if path]
        return result


class ProcessJbossEapChkconfig(util.InitLineFinder):
    """Process the output of 'chkconfig'."""

    DEPS = ["internal_have_chkconfig"]
    KEY = "jboss_eap_chkconfig"
    KEYWORDS = ["jboss", "eap"]


class ProcessJbossEapSystemctl(util.InitLineFinder):
    """Process the output of 'systemctl list-unit-files'."""

    DEPS = ["internal_have_systemctl"]
    KEY = "jboss_eap_systemctl_unit_files"
    KEYWORDS = ["jboss", "eap"]


class ProcessEapHomeLs(util.IndicatorFileFinder):
    """Process the output of 'ls -1 ...'."""

    KEY = "eap_home_ls"

    INDICATOR_FILES = ["JBossEULA.txt", "version.txt"]


class ProcessEapHomeVersionTxt(util.PerItemProcessor):
    """Extract the version from an EAP version.txt file."""

    KEY = "eap_home_version_txt"
    VERSION_RE = re.compile(
        r"Red Hat JBoss Enterprise Application Platform - Version (.*)\.GA"
    )

    @staticmethod
    def process_item(item):
        """Extract just the version number."""
        if item.get("rc", True):
            return False
        match = ProcessEapHomeVersionTxt.VERSION_RE.match(item["stdout"].strip())
        if match:
            return match.group(1)

        # If we found a version.txt file, this likely *is* JBoss EAP,
        # it's just a version file format that we don't recognize. If
        # we return it unchanged, the fingerprinter will prepend
        # 'Unknown-version: ' and count it as found.
        return item["stdout"].strip()


class ProcessEapHomeReadmeTxt(util.StdoutSearchProcessor):
    """Process the output of 'cat .../README.txt'."""

    KEY = "eap_home_readme_txt"
    SEARCH_STRING = "Welcome to WildFly"


class ProcessJbossModulesManifestMf(util.StdoutPassthroughProcessor):
    """Process the jboss-modules.jar MANIFEST.MF file's contents."""

    KEY = "eap_home_jboss_modules_manifest"


class ProcessJbossModulesVersion(util.StdoutPassthroughProcessor):
    """Process the output of 'java -jar jboss-modules.jar -version'."""

    KEY = "eap_home_jboss_modules_version"


class ProcessEapHomeBinForFuse(util.IndicatorFileFinder):
    """Process the output of 'ls -1' for eap_home_bin to check for fuse."""

    KEY = "eap_home_bin"

    INDICATOR_FILES = ["fuseconfig.sh", "fusepatch.sh"]


class ItemSuccessChecker(util.PerItemProcessor):
    """Check whether each item succeeded."""

    KEY = None

    @staticmethod
    def process_item(item):
        """Check whether the item succeeded."""
        return item.get("rc", 1) == 0


class ProcessEapHomeLayers(ItemSuccessChecker):
    """Process the output of eap home layers."""

    KEY = "eap_home_layers"


class ProcessEapHomeLayersConf(ItemSuccessChecker):
    """Process the output of eap home layers conf."""

    KEY = "eap_home_layers_conf"


class ProcessFindJbossEAPJarVer(util.FindJarVer):
    """Process the results of a find jar version command."""

    KEY = "jboss_eap_jar_ver"


class ProcessFindJbossEAPRunJarVer(util.FindJarVer):
    """Process the results of a find jar version command."""

    KEY = "jboss_eap_run_jar_ver"
