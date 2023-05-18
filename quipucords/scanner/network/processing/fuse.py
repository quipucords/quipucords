"""Initial processing of the shell output from the jboss_fuse_on_karaf role."""

import logging

from scanner.network.processing import util

logger = logging.getLogger(__name__)

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
