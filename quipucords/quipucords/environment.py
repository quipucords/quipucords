#
# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#

"""Gets system environment data."""

import logging
import os
import platform
import subprocess
import sys

# pylint: disable=invalid-name
# Get an instance of a logger
logger = logging.getLogger(__name__)


def commit():
    """Collect the build number for the server.

    :returns: A build number
    """
    commit_info = os.environ.get('QUIPUCORDS_COMMIT', None)
    if commit_info is None:
        try:
            commit_info = subprocess.check_output(['git',
                                                   'describe',
                                                   '--always']).strip()
            commit_info = commit_info.decode('utf-8')
        except Exception:  # pylint: disable=broad-except
            pass
    return commit_info


def platform_info():
    """Collect the platform information.

    :returns: A dictionary of platform data
    """
    return platform.uname()._asdict()


def python_version():
    """Collect the python version information.

    :returns: The python version string.
    """
    return sys.version.replace('\n', '')


def modules():
    """Collect the installed modules.

    :returns: A dictonary of module names and versions.
    """
    module_data = {}
    for name, module in sorted(sys.modules.items()):
        if hasattr(module, '__version__'):
            module_data[str(name)] = str(module.__version__)
    return module_data


def init_server_identifier():
    """Create or retreive server's global identifier."""
    from api.status.model import ServerInformation

    server_id = ServerInformation.create_or_retreive_server_id()
    logger.info('Server ID: %s',
                server_id)


def startup():
    """Log environment at startup."""
    # pylint: disable=too-many-locals
    logger.info('Platform:')
    for name, value in platform_info().items():
        logger.info('%s - %s ', name, value)

    logger.info('Python: %s', python_version())
    module_list = []
    for name, value in modules().items():
        mod = '{} - {}'.format(name, value)
        module_list.append(mod)

    logger.info('Modules: %s', ', '.join(module_list))
    env_list = []
    for key, value in os.environ.items():
        env = '{} - {}'.format(key, value)
        env_list.append(env)
    mark = '-' * 20
    logger.info('%s BEGIN ENVIRONMENT VARIABLES %s', mark, mark)
    logger.info('\n'.join(env_list))
    logger.info('%s END ENVIRONMENT VARIABLES %s', mark, mark)

    QPC_POSTGRES_DBMS = 'postgres'
    QPC_SQLITE_DBMS = 'sqlite'
    valid_dbms = [QPC_POSTGRES_DBMS, QPC_SQLITE_DBMS]
    qpc_dbms = os.environ.get('QPC_DBMS')
    if qpc_dbms in valid_dbms:
        logger.info('QPC_DBMS set to "%s".', qpc_dbms)
        if qpc_dbms == QPC_POSTGRES_DBMS:
            database = os.getenv('QPC_DBMS_DATABASE', 'postgres')
            user = os.getenv('QPC_DBMS_USER', 'postgres')
            host = os.getenv('QPC_DBMS_HOST', 'localhost' or '::')
            port = os.getenv('QPC_DBMS_PORT', 5432)
            logger.info('QPC_DBMS_HOST set to "%s"', host)
            logger.info('QPC_DBMS_PORT set to "%s"', port)
            logger.info('QPC_DBMS_DATABASE set to "%s"', database)
            logger.info('QPC_DBMS_USER set to "%s"', user)
    elif not qpc_dbms:
        logger.info('QPC_DBMS not set. Using default of "sqlite".')
    else:
        logger.info('QPC_DBMS was set to "%s" which is not a valid option. '
                    'Using default of "sqlite.',
                    (qpc_dbms))

    logger.info('Commit: %s', commit())
    init_server_identifier()
