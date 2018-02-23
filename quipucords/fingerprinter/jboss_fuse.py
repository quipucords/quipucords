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

"""Ingests raw facts to determine the status of JBoss Fuse for a system."""

import logging
from api.models import Product, Source
from fingerprinter.utils import product_entitlement_found

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

PRODUCT = 'JBoss Fuse'
PRESENCE_KEY = 'presence'
RAW_FACT_KEY = 'raw_fact_key'
META_DATA_KEY = 'metadata'
JBOSS_FUSE_FUSE_ON_EAP = 'eap_home_bin'
JBOSS_FUSE_ON_KARAF_KARAF_HOME = 'karaf_home_bin_fuse'
JBOSS_FUSE_SYSTEMCTL_FILES = 'jboss_fuse_systemctl_unit_files'
JBOSS_FUSE_CHKCONFIG = 'jboss_fuse_chkconfig'
SUBMAN_CONSUMED = 'subman_consumed'
ENTITLEMENTS = 'entitlements'


def detect_jboss_fuse(source, facts):
    """Detect if JBoss Fuse is present based on system facts.

    :param source: The source of the facts
    :param facts: facts for a system
    :returns: dictionary defining the product presence
    """
    fuse_on_eap = facts.get(JBOSS_FUSE_FUSE_ON_EAP)
    fuse_on_karaf = facts.get(JBOSS_FUSE_ON_KARAF_KARAF_HOME)
    systemctl_files = facts.get(JBOSS_FUSE_SYSTEMCTL_FILES)
    chkconfig = facts.get(JBOSS_FUSE_CHKCONFIG)
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

    if ((fuse_on_eap and any(fuse_on_eap.values())) or
            (fuse_on_karaf and any(fuse_on_karaf.values()))):
        raw_fact_key = '{}/{}'.format(JBOSS_FUSE_FUSE_ON_EAP,
                                      JBOSS_FUSE_ON_KARAF_KARAF_HOME)
        metadata[RAW_FACT_KEY] = raw_fact_key
        product_dict[PRESENCE_KEY] = Product.PRESENT
    elif systemctl_files or chkconfig:
        raw_fact_key = '{}/{}'.format(
            JBOSS_FUSE_SYSTEMCTL_FILES,
            JBOSS_FUSE_CHKCONFIG)
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
