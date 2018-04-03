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


def startup():
    """Log environment at startup."""
    logger.info('Platform:')
    for name, value in platform_info().items():
        logger.info('%s - %s ', name, value)

    logger.info('Python: %s', python_version())
    module_list = []
    for name, value in modules().items():
        mod = '{} - {}'.format(name, value)
        module_list.append(mod)

    logger.info('Modules: %s', ', '.join(module_list))
    logger.info('Commit: %s', commit())
