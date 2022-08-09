# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Initial processing of the shell output from the jboss_fuse_on_karaf role."""

import logging

from scanner.network.processing import util

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# pylint: disable=too-few-public-methods

# #### Processors ####


class ProcessFindJbossActiveMQJar(util.FindJar):
    """Process the results of a find jar command."""

    KEY = "jboss_activemq_ver"


class ProcessFindJbossCamelJar(util.FindJar):
    """Process the results of a find jar command."""

    KEY = "jboss_camel_ver"


class ProcessFindJbossCXFJar(util.FindJar):
    """Process the results of a find jar command."""

    KEY = "jboss_cxf_ver"
