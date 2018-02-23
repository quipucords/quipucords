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

"""Ingests raw facts to determine the status of JBoss EAP for a system."""

import logging
from api.models import Product, Source
from fingerprinter.utils import product_entitlement_found

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

PRODUCT = 'JBoss EAP'
PRESENCE_KEY = 'presence'
RAW_FACT_KEY = 'raw_fact_key'
META_DATA_KEY = 'metadata'
JBOSS_EAP_RUNNING_PATHS = 'jboss_eap_running_paths'
JBOSS_EAP_JBOSS_USER = 'jboss_eap_id_jboss'
JBOSS_EAP_COMMON_FILES = 'jboss_eap_common_files'
JBOSS_EAP_PROCESSES = 'jboss_eap_processes'
JBOSS_EAP_PACKAGES = 'jboss_eap_packages'
JBOSS_EAP_LOCATE_JBOSS_MODULES_JAR = 'jboss_eap_locate_jboss_modules_jar'
JBOSS_EAP_SYSTEMCTL_FILES = 'jboss_eap_systemctl_unit_files'
JBOSS_EAP_CHKCONFIG = 'jboss_eap_chkconfig'
JBOSS_EAP_EAP_HOME = 'eap_home_ls'
SUBMAN_CONSUMED = 'subman_consumed'
ENTITLEMENTS = 'entitlements'


# pylint: disable=too-many-locals
def detect_jboss_eap(source, facts):
    """Detect if JBoss EAP is present based on system facts.

    :param source: The source of the facts
    :param facts: facts for a system
    :returns: dictionary defining the product presence
    """
    running_paths = facts.get(JBOSS_EAP_RUNNING_PATHS)
    jboss_user = facts.get(JBOSS_EAP_JBOSS_USER)
    common_files = facts.get(JBOSS_EAP_COMMON_FILES)
    eap_processes = facts.get(JBOSS_EAP_PROCESSES)
    packages = facts.get(JBOSS_EAP_PACKAGES)
    modules_jar = facts.get(JBOSS_EAP_LOCATE_JBOSS_MODULES_JAR)
    systemctl_files = facts.get(JBOSS_EAP_SYSTEMCTL_FILES)
    chkconfig = facts.get(JBOSS_EAP_CHKCONFIG)
    eap_home = facts.get(JBOSS_EAP_EAP_HOME)
    subman_consumed = facts.get(SUBMAN_CONSUMED, [])
    entitlements = facts.get(ENTITLEMENTS, [])

    source_object = Source.objects.filter(id=source.get('source_id')).first()
    if source_object:
        source_name = source_object.name
    else:
        source_name = None

    metadata = {
        'source_id': source['source_id'],
        'source_name': source_name,
        'source_type': source['source_type'],
    }
    product_dict = {'name': PRODUCT}

    if (running_paths or
            packages or
            modules_jar or
            eap_home):
        raw_fact_key = '{}/{}/{}/{}'.format(JBOSS_EAP_RUNNING_PATHS,
                                            JBOSS_EAP_PACKAGES,
                                            JBOSS_EAP_LOCATE_JBOSS_MODULES_JAR,
                                            JBOSS_EAP_EAP_HOME)
        metadata[RAW_FACT_KEY] = raw_fact_key
        product_dict[PRESENCE_KEY] = Product.PRESENT
    elif (jboss_user or
          common_files or
          eap_processes or
          systemctl_files or
          chkconfig):
        raw_fact_key = '{}/{}/{}/{}/{}'.format(
            JBOSS_EAP_JBOSS_USER,
            JBOSS_EAP_COMMON_FILES,
            JBOSS_EAP_PROCESSES,
            JBOSS_EAP_SYSTEMCTL_FILES,
            JBOSS_EAP_CHKCONFIG)
        metadata[RAW_FACT_KEY] = raw_fact_key
        product_dict[PRESENCE_KEY] = Product.POTENTIAL
    elif product_entitlement_found(subman_consumed, PRODUCT):
        metadata[RAW_FACT_KEY] = SUBMAN_CONSUMED
        product_dict[PRESENCE_KEY] = Product.POTENTIAL
    elif product_entitlement_found(entitlements, PRODUCT):
        metadata[RAW_FACT_KEY] = ENTITLEMENTS
        product_dict[PRESENCE_KEY] = Product.POTENTIAL
    else:
        metadata[RAW_FACT_KEY] = ''
        product_dict[PRESENCE_KEY] = Product.ABSENT

    product_dict[META_DATA_KEY] = metadata
    return product_dict
