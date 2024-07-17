"""Initial processing of the shell output from the user_data role."""

from scanner.network.processing import process


class ProcessSystemUserCount(process.Processor):
    """Process the system_user_count fact."""

    KEY = "system_user_count"

    DEPS = ["internal_system_user_count"]
    REQUIRE_DEPS = False

    @staticmethod
    def process(output, dependencies):
        """Pass the output back through."""
        system_user_count = dependencies.get("internal_system_user_count")
        if system_user_count and system_user_count.get("rc") == 0:
            # differentiate between system and regular users
            users = [
                line
                for line in system_user_count.get("stdout_lines")
                if "/sbin/nologin" not in line
                and ("/home/" in line or "/root:/" in line)
            ]
            unique_users = set(users)
            return len(unique_users)
        return ""
