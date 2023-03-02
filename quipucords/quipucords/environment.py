"""Gets system environment data."""

import logging
import os
import platform
import subprocess
import sys
from functools import cache

from quipucords.release import infer_version

# pylint: disable=invalid-name
# Get an instance of a logger
logger = logging.getLogger(__name__)


def commit():
    """Collect the commit for the server."""
    commit_info = os.environ.get("QUIPUCORDS_COMMIT", "").strip()
    if not commit_info:
        try:
            commit_info = subprocess.check_output(
                ["git", "rev-parse", "--verify", "HEAD"]
            ).strip()
            commit_info = commit_info.decode("utf-8")
        except Exception:  # pylint: disable=broad-except
            pass
    return commit_info


@cache
def server_version():
    """Return server version."""
    return f"{infer_version()}.{commit()}"


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


def modules():
    """Collect the installed modules.

    :returns: A dictonary of module names and versions.
    """
    module_data = {}
    for name, module in sorted(sys.modules.items()):
        if hasattr(module, "__version__"):
            module_data[str(name)] = str(module.__version__)
    return module_data


def init_server_identifier():
    """Create or retrieve server's global identifier."""
    # pylint: disable=import-outside-toplevel
    from api.status.model import ServerInformation

    server_id = ServerInformation.create_or_retrieve_server_id()
    logger.info("Server ID: %s", server_id)


def start_debugger_if_required():
    """Start a debugger session if QPC_DEBUGPY envvar is set."""
    # pylint: disable=import-outside-toplevel
    DEBUG_PY = int(os.environ.get("QPC_DEBUGPY", "0"))
    DEBUG_PY_PORT = int(os.environ.get("QPC_DEBUGPY_PORT", "5678"))
    if DEBUG_PY:
        try:
            import debugpy
        except ImportError:
            logger.exception("debugpy is not installed, can't start debugger.")
            return

        debugpy.listen(("0.0.0.0", DEBUG_PY_PORT))
        print("⏳ debugpy debugger can now be attached ⏳", flush=True)


def startup():
    """Log environment at startup."""
    # pylint: disable=too-many-locals
    start_debugger_if_required()
    logger.info("Platform:")
    for name, value in platform_info().items():
        logger.info("%s - %s ", name, value)

    logger.info("Python: %s", python_version())
    module_list = []
    for name, value in modules().items():
        mod = f"{name} - {value}"
        module_list.append(mod)

    logger.info("Modules: %s", ", ".join(module_list))
    env_list = []
    for key, value in os.environ.items():
        if "password" in key.lower():
            value = "*" * 8
        env = f"{key} - {value}"
        env_list.append(env)
    mark = "-" * 20
    logger.info("%s BEGIN ENVIRONMENT VARIABLES %s", mark, mark)
    logger.info("\n".join(env_list))
    logger.info("%s END ENVIRONMENT VARIABLES %s", mark, mark)

    QPC_POSTGRES_DBMS = "postgres"
    QPC_SQLITE_DBMS = "sqlite"
    valid_dbms = [QPC_POSTGRES_DBMS, QPC_SQLITE_DBMS]
    qpc_dbms = os.environ.get("QPC_DBMS")
    if qpc_dbms in valid_dbms:
        logger.info('QPC_DBMS set to "%s".', qpc_dbms)
        if qpc_dbms == QPC_POSTGRES_DBMS:
            database = os.getenv("QPC_DBMS_DATABASE", "postgres")
            user = os.getenv("QPC_DBMS_USER", "postgres")
            host = os.getenv("QPC_DBMS_HOST", "localhost" or "::")
            # pylint: disable=invalid-envvar-default
            port = os.getenv("QPC_DBMS_PORT", 5432)
            logger.info('QPC_DBMS_HOST set to "%s"', host)
            logger.info('QPC_DBMS_PORT set to "%s"', port)
            logger.info('QPC_DBMS_DATABASE set to "%s"', database)
            logger.info('QPC_DBMS_USER set to "%s"', user)
    elif not qpc_dbms:
        logger.info('QPC_DBMS not set. Using default of "postgres".')
    else:
        logger.info(
            'QPC_DBMS was set to "%s" which is not a valid option. '
            'Using default of "postgres".',
            (qpc_dbms),
        )

    logger.info("Server version: %s", server_version())
    logger.info("Commit: %s", commit())
    init_server_identifier()
