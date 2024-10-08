"""Gets system environment data."""

import logging
import os
import platform
import subprocess
import sys
from functools import cache

from django.conf import settings

from quipucords.release import infer_version

logger = logging.getLogger(__name__)


def commit():
    """Collect the commit for the server."""
    commit_info = os.environ.get("QUIPUCORDS_COMMIT", "").strip()
    if not commit_info:
        commit_info = subprocess.check_output(  # noqa: S603
            ["git", "rev-parse", "--verify", "HEAD"]  # noqa: S607
        ).strip()
        commit_info = commit_info.decode("utf-8")
    return commit_info


@cache
def server_version():
    """Return server version."""
    return f"{infer_version()}+{commit()}"


def platform_info():
    """Collect the platform information.

    :returns: A dictionary of platform data
    """
    return platform.uname()._asdict()


def python_version():
    """Collect the python version information.

    :returns: The python version string.
    """
    return sys.version.replace("\n", "")


def init_server_identifier():
    """Create or retrieve server's global identifier."""
    from api.status.model import ServerInformation

    server_id = ServerInformation.create_or_retrieve_server_id()
    logger.info("Server ID: %s", server_id)


def log_system_info():
    """Log system information."""
    logger.info("Platform:")
    for name, value in platform_info().items():
        logger.info("%s - %s ", name, value)

    logger.info("Python: %s", python_version())


def log_all_environment_variables():
    """
    Log all environment variables.

    Note: This is potentially a catastrophically bad idea and risks leaking sensitive
    values that don't contain "password" in their names. Use with extreme caution.
    """
    if not settings.QUIPUCORDS_LOG_ALL_ENV_VARS_AT_STARTUP:
        return
    env_list = []
    for key, value in os.environ.items():
        if "password" in key.lower():
            value = "*" * 8  # noqa: PLW2901
        env = f"{key} - {value}"
        env_list.append(env)
    mark = "-" * 20
    logger.info("%s BEGIN ENVIRONMENT VARIABLES %s", mark, mark)
    logger.info("\n".join(sorted(env_list)))
    logger.info("%s END ENVIRONMENT VARIABLES %s", mark, mark)


def log_database_configuration():
    """Log settings related to the database configuration."""
    settings_to_log = {
        "postgres": [
            "QUIPUCORDS_DBMS",
            "QUIPUCORDS_DBMS_HOST",
            "QUIPUCORDS_DBMS_PORT",
            "QUIPUCORDS_DBMS_DATABASE",
            "QUIPUCORDS_DBMS_USER",
        ],
        "sqlite": [
            "QUIPUCORDS_DBMS",
            "DB_PATH",
        ],
    }

    for setting_name in settings_to_log[settings.QUIPUCORDS_DBMS]:
        logger.info("%s set to %s", setting_name, repr(getattr(settings, setting_name)))


def log_redis_configuration():
    """Log settings related to the Redis configuration."""
    settings_to_log = ["REDIS_USERNAME", "REDIS_HOST", "REDIS_PORT"]
    for setting_name in settings_to_log:
        logger.info("%s set to %s", setting_name, repr(getattr(settings, setting_name)))


def log_server_version():
    """Log the server version."""
    logger.info("Server version: %s", server_version())
    logger.info("Commit: %s", commit())
    init_server_identifier()


def startup():
    """Log environment information at startup."""
    log_system_info()
    log_all_environment_variables()
    log_database_configuration()
    log_redis_configuration()
    log_server_version()
