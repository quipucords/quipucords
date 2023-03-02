"""Initial processing of raw shell output from Ansible commands."""

from scanner.network.processing import process


# pylint: disable=too-few-public-methods
class ProcessJWSInstalledWithRpm(process.Processor):
    """Process the results of 'yum grouplist jws3 jws3plus jws5...'."""

    KEY = "jws_installed_with_rpm"
    RETURN_CODE_ANY = True

    @staticmethod
    def process(output, dependencies=None):
        """Determine if jws was installed with rpm. Version 3 and up."""
        stdout = output.get("stdout_lines", [])
        if len(stdout) == 1 and "Red Hat JBoss Web Server" in stdout[0]:
            return True
        return False


# pylint: disable=too-few-public-methods
class ProcessHasJBossEULA(process.Processor):
    """Process result of $(ls $JWS_HOME/JBossEULA.txt)."""

    KEY = "jws_has_eula_txt_file"

    @staticmethod
    def process(output, dependencies=None):
        """Check if JBossEULA.txt exists in JWS_Home directory."""
        stdout = output.get("stdout", "false")
        return stdout == "true"


# pylint: disable=too-few-public-methods
class ProcessTomcatPartOfRedhatProduct(process.Processor):
    """Process output of search for redhat string in tomcat files."""

    KEY = "tomcat_is_part_of_redhat_product"

    @staticmethod
    def process(output, dependencies=None):
        """Return either True or False."""
        result = output.get("stdout_lines", False)
        if result and result[0] == "True":
            return True
        return False


# pylint: disable=too-few-public-methods
class ProcessJWSHasCert(process.Processor):
    """Process output of 'ls /etc/pki/product/185.pem 2>/dev/null'."""

    KEY = "jws_has_cert"
    RETURN_CODE_ANY = True

    @staticmethod
    def process(output, dependencies=None):
        """Return either True or False."""
        if output.get("stdout_lines", False):
            return True
        return False
