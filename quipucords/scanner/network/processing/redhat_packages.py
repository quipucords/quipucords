# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Initial processing of the shell output from the redhat_packages role."""

import logging

from scanner.network.processing import process

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# pylint: disable=too-few-public-methods

# #### Processors ####


class ProcessRedHatPackagesCerts(process.Processor):
    """Process the redhat packages certs."""

    KEY = "redhat_packages_certs"

    @staticmethod
    def process(output, dependencies=None):
        """Pass the output back through."""
        if output.get("rc", True):
            return ""
        certs = output.get("stdout")
        if certs:
            if certs[-1] == ";":
                certs = certs[:-1]
        return certs
