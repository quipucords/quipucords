# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Initial processing of the shell output from the cpu role."""

import logging

from scanner.network.processing import process
from scanner.network.processing.util import get_line

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# pylint: disable=too-few-public-methods

# #### Processors ####


class ProcessCpuModelVer(process.Processor):
    """Process the model version of the cpu."""

    KEY = 'cpu_model_ver'

    @staticmethod
    def process(output):
        """Pass the output back through."""
        return get_line(output['stdout_lines'])


class ProcessCpuCpuFamily(process.Processor):
    """Process the cpu family."""

    KEY = 'cpu_cpu_family'

    @staticmethod
    def process(output):
        """Pass the output back through."""
        return get_line(output['stdout_lines'])


class ProcessCpuVendorId(process.Processor):
    """Process the vendor id of the cpu."""

    KEY = 'cpu_vendor_id'

    @staticmethod
    def process(output):
        """Pass the output back through."""
        return get_line(output['stdout_lines'])


class ProcessCpuModelName(process.Processor):
    """Process the model name of the cpu."""

    KEY = 'cpu_model_name'

    @staticmethod
    def process(output):
        """Pass the output back through."""
        return get_line(output['stdout_lines'])


class ProcessCpuBogomips(process.Processor):
    """Process the bogomips of the cpu."""

    KEY = 'cpu_bogomips'

    @staticmethod
    def process(output):
        """Pass the output back through."""
        return get_line(output['stdout_lines'])
