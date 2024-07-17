"""Initial processing of raw shell output from Ansible commands."""

from scanner.network.processing import process


class ProcessJWSInstalledWithRpm(process.Processor):
    """Process the results of 'yum grouplist jws3 jws3plus jws5...'."""

    KEY = "jws_installed_with_rpm"
    RETURN_CODE_ANY = True

    @staticmethod
    def process(output, dependencies=None):
        """Determine if jws was installed with rpm. Version 3 and up."""
        stdout_lines = output.get("stdout_lines", [])
        return bool(stdout_lines and "Red Hat JBoss Web Server" in stdout_lines[-1])


class ProcessHasJBossEULA(process.Processor):
    """Process result of $(ls $JWS_HOME/JBossEULA.txt)."""

    KEY = "jws_has_eula_txt_file"

    @staticmethod
    def process(output, dependencies=None):
        """Check if JBossEULA.txt exists in JWS_Home directory."""
        stdout_lines = output.get("stdout_lines", [])
        return bool(stdout_lines and stdout_lines[-1] == "true")


class ProcessJWSHasCert(process.Processor):
    """Process output of 'ls /etc/pki/product/185.pem 2>/dev/null'."""

    KEY = "jws_has_cert"
    RETURN_CODE_ANY = True

    @staticmethod
    def process(output, dependencies=None):
        """Return either True or False."""
        stdout_lines = output.get("stdout_lines", [])
        return bool(stdout_lines and stdout_lines[-1].endswith(".pem"))
