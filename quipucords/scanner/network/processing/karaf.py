"""Initial processing of the shell output from the jboss_fuse_on_karaf role."""

import logging

from scanner.network.processing import process, util

logger = logging.getLogger(__name__)

# #### Processors ####

FIND_WARNING = (
    "find: WARNING: Hard link count is wrong for /proc: this may"
    " be a bug in your filesystem driver."
)


class ProcessKarafRunningProcesses(process.Processor):
    """Process a list of Jboss Fuse on Karaf processes."""

    KEY = "karaf_running_processes"

    @staticmethod
    def process(output, dependencies=None):
        """Preserve the output except for a known issue."""
        if FIND_WARNING in output["stdout"]:
            logging.error("Find command failed")
            return process.NO_DATA

        return output["stdout"].strip()


class ProcessFindKaraf(process.Processor):
    """Process the results of a find command."""

    KEY = "karaf_find_karaf_jar"

    @staticmethod
    def process(output, dependencies=None):
        """Return the command's output."""
        return output["stdout_lines"]


class ProcessLocateKaraf(process.Processor):
    """Process the output of 'locate jboss.fuse-on-karaf.karaf-home'."""

    KEY = "karaf_locate_karaf_jar"

    DEPS = ["internal_have_locate"]

    @staticmethod
    def process(output, dependencies=None):
        """Pass the output back through."""
        result = [jar for jar in output.get("stdout_lines", []) if jar.strip()]
        return result


class ProcessJbossFuseChkconfig(util.InitLineFinder):
    """Process the output of 'chkconfig'."""

    DEPS = ["internal_have_chkconfig"]
    KEY = "jboss_fuse_chkconfig"
    KEYWORDS = ["fuse"]


class ProcessJbossFuseSystemctl(util.InitLineFinder):
    """Process the output of 'systemctl list-unit-files'."""

    DEPS = ["internal_have_systemctl"]
    KEY = "jboss_fuse_systemctl_unit_files"
    KEYWORDS = ["fuse"]
    IGNORE_WORDS = ["sys-fs-fuse-connections.mount"]


class ProcessKarafHomeBinFuse(process.Processor):
    """Process karaf home indicators to detect Fuse-on-Karaf."""

    KEY = "karaf_home_bin_fuse"

    @staticmethod
    def process(output, dependencies=None):
        """Pass the output back through."""
        return {
            result["item"]: result.get("rc", 1) == 0 for result in output["results"]
        }


class ProcessKarafHomeSystemOrgJboss(process.Processor):
    """Process the karaf_home_system_org_jboss fact."""

    KEY = "karaf_home_system_org_jboss"

    @staticmethod
    def process(output, dependencies=None):
        """Pass the output back through."""
        return {
            str(result["stdout_lines"]): result.get("rc", 1) == 0
            for result in output["results"]
        }


class FuseVersionProcessor(process.Processor):
    """Pass the item name and std out to the fingerprinter.

    Used for with_items tasks when looking for fuse version
    """

    KEY = None

    @staticmethod
    def process(output, dependencies=None):
        """Process the output of a with_items task from Ansible.

        :param output: the output of a with_items task.

        :returns: a list containing dictionaries defining the home
        directory and version, or an empty list
        """
        results = []
        for item in output["results"]:
            result = {}
            item_name = item.get("item")
            if item_name:
                if item.get("rc", True):
                    pass
                else:
                    if item.get("stdout", "").strip() != "":  # noqa: PLR5501, PLC1901
                        value = [
                            version
                            for version in item.get("stdout_lines", [])
                            if version.strip()
                        ]
                        result["install_home"] = item_name
                        result["version"] = list(set(value))
                if result:
                    results.append(result)
        return results


class FuseVersionProcessorLocate(process.Processor):
    """Pass stdout lines to the fingerprinter.

    Used for locate tasks when looking for fuse version
    """

    KEY = None

    @staticmethod
    def process(output, dependencies=None):
        """Process the output of a with_items task from Ansible.

        :param output: the output of a with_items task.

        :returns: a list containing the version or an empty list
        """
        results = []
        if output.get("rc", 1) == 0 and output.get("stdout", "").strip() != [""]:

            results = list(
                set([line for line in output.get("stdout_lines", []) if line.strip()])
            )
        return results


class ProcessJbossFuseCamelVersion(FuseVersionProcessor):
    """Process the output of looking for camel version'."""

    KEY = "jboss_fuse_on_karaf_camel_ver"


class ProcessJbossFuseActivemqVersion(FuseVersionProcessor):
    """Process the output of looking for activemq version'."""

    KEY = "jboss_fuse_on_karaf_activemq_ver"


class ProcessJbossFuseCxfVersion(FuseVersionProcessor):
    """Process the output of looking for cxf version'."""

    KEY = "jboss_fuse_on_karaf_cxf_ver"


class ProcessJbossFuseOnEapCamelVersion(FuseVersionProcessor):
    """Process the output of looking for camel version'."""

    KEY = "jboss_fuse_on_eap_camel_ver"


class ProcessJbossFuseOnEapActivemqVersion(FuseVersionProcessor):
    """Process the output of looking for activemq version'."""

    KEY = "jboss_fuse_on_eap_activemq_ver"


class ProcessJbossFuseOnEapCxfVersion(FuseVersionProcessor):
    """Process the output of looking for cxf version'."""

    KEY = "jboss_fuse_on_eap_cxf_ver"


class ProcessLocateCamel(FuseVersionProcessorLocate):
    """Process the output of 'locate camel-core'."""

    KEY = "jboss_fuse_camel_ver"
    DEPS = ["internal_have_locate"]


class ProcessLocateActivemq(FuseVersionProcessorLocate):
    """Process the output of 'locate activemq'."""

    KEY = "jboss_fuse_activemq_ver"
    DEPS = ["internal_have_locate"]


class ProcessLocateCxf(FuseVersionProcessorLocate):
    """Process the output of 'locate cxf-rt'."""

    KEY = "jboss_fuse_cxf_ver"
    DEPS = ["internal_have_locate"]
