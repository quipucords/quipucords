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

from api.models import Product
from fingerprinter.constants import META_DATA_KEY, PRESENCE_KEY
from fingerprinter.utils import generate_raw_fact_members, product_entitlement_found
from utils import default_getter

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

PRODUCT = "JBoss Fuse"
VERSION_KEY = "version"
RAW_FACT_KEY = "raw_fact_key"
EAP_HOME_BIN = "eap_home_bin"
KARAF_HOME_BIN_FUSE = "karaf_home_bin_fuse"
JBOSS_FUSE_SYSTEMCTL_FILES = "jboss_fuse_systemctl_unit_files"
JBOSS_FUSE_CHKCONFIG = "jboss_fuse_chkconfig"
SUBMAN_CONSUMED = "subman_consumed"
ENTITLEMENTS = "entitlements"
# versions from fuse on eap or karaf
FUSE_ACTIVEMQ_VERSION = "fuse_activemq_version"
FUSE_CAMEL_VERSION = "fuse_camel_version"
FUSE_CXF_VERSION = "fuse_cxf_version"
# versions from fuse on eap
JBOSS_FUSE_ON_EAP_ACTIVEMQ_VER = "jboss_fuse_on_eap_activemq_ver"
JBOSS_FUSE_ON_EAP_CAMEL_VER = "jboss_fuse_on_eap_camel_ver"
JBOSS_FUSE_ON_EAP_CXF_VER = "jboss_fuse_on_eap_cxf_ver"
# versions from extended-products scan
JBOSS_ACTIVEMQ_VER = "jboss_activemq_ver"
JBOSS_CAMEL_VER = "jboss_camel_ver"
JBOSS_CXF_VER = "jboss_cxf_ver"


FUSE_CLASSIFICATIONS = {
    "redhat-630187": "Fuse-6.3.0",
    "redhat-621084": "Fuse-6.2.1",
    "redhat-620133": "Fuse-6.2.0",
    "redhat-611412": "Fuse-6.1.1",
    "redhat-610379": "Fuse-6.1.0",
    "redhat-60024": "Fuse-6.0.0",
}


def get_version(eap_version):
    """Return the version found for fuse-on-home-dir facts.

    :param: eap_version: A list containing dictionaries
    mapping install dirs and versions
    :returns a list of versions
    """
    new_versions = []
    for dictionary in eap_version:
        new_versions.append(dictionary["version"])
    # at this point we have a nested list of versions and we want it
    # to be a flat list
    new_versions = [item for items in new_versions for item in items]
    return new_versions


# pylint: disable=R0914, too-many-statements
def detect_jboss_fuse(source, facts):
    """Detect if JBoss Fuse is present based on system facts.

    :param source: The source of the facts
    :param facts: dictionary of facts for a system
    :returns: dictionary defining the product presence
    """
    eap_home_bin = facts.get(EAP_HOME_BIN)
    karaf_home_bin_fuse = facts.get(KARAF_HOME_BIN_FUSE)
    systemctl_files = facts.get(JBOSS_FUSE_SYSTEMCTL_FILES)
    chkconfig = facts.get(JBOSS_FUSE_CHKCONFIG)
    subman_consumed = default_getter(facts, SUBMAN_CONSUMED, [])
    entitlements = default_getter(facts, ENTITLEMENTS, [])
    # Get activemq versions
    fuse_activemq = default_getter(facts, FUSE_ACTIVEMQ_VERSION, [])
    eap_activemq = get_version(
        default_getter(facts, JBOSS_FUSE_ON_EAP_ACTIVEMQ_VER, [])
    )
    ext_fuse_activemq = default_getter(facts, JBOSS_ACTIVEMQ_VER, [])
    activemq_list = fuse_activemq + eap_activemq + ext_fuse_activemq
    # Get camel-core versions
    fuse_camel = default_getter(facts, FUSE_CAMEL_VERSION, [])
    eap_camel = get_version(default_getter(facts, JBOSS_FUSE_ON_EAP_CAMEL_VER, []))
    ext_fuse_camel = default_getter(facts, JBOSS_CAMEL_VER, [])
    camel_list = fuse_camel + eap_camel + ext_fuse_camel
    # Get cxf-rt versions
    fuse_cxf = default_getter(facts, FUSE_CXF_VERSION, [])
    eap_cxf = get_version(default_getter(facts, JBOSS_FUSE_ON_EAP_CXF_VER, []))
    ext_fuse_cxf = default_getter(facts, JBOSS_CXF_VER, [])

    cxf_list = fuse_cxf + eap_cxf + ext_fuse_cxf
    fuse_versions = []

    metadata = {
        "server_id": source["server_id"],
        "source_name": source["source_name"],
        "source_type": source["source_type"],
    }
    product_dict = {"name": PRODUCT}
    raw_facts = None

    is_fuse_on_eap = eap_home_bin and any(eap_home_bin.values())
    is_fuse_on_karaf = karaf_home_bin_fuse and any(karaf_home_bin_fuse.values())
    if (
        (activemq_list and camel_list and cxf_list)
        or is_fuse_on_eap
        or is_fuse_on_karaf
    ):
        # Set versions from extended-products scan & regular scan
        fuse_versions = list(
            set(
                fuse_activemq
                + eap_activemq
                + ext_fuse_activemq
                + fuse_camel
                + eap_camel
                + ext_fuse_camel
                + fuse_cxf
                + eap_cxf
                + ext_fuse_cxf
            )
        )
    if is_fuse_on_eap or is_fuse_on_karaf or fuse_versions:
        raw_facts_dict = {
            EAP_HOME_BIN: is_fuse_on_eap,
            KARAF_HOME_BIN_FUSE: is_fuse_on_karaf,
            JBOSS_ACTIVEMQ_VER: ext_fuse_activemq,
            JBOSS_CAMEL_VER: ext_fuse_camel,
            JBOSS_CXF_VER: ext_fuse_cxf,
            FUSE_ACTIVEMQ_VERSION: fuse_activemq,
            FUSE_CAMEL_VERSION: fuse_camel,
            FUSE_CXF_VERSION: fuse_cxf,
            JBOSS_FUSE_ON_EAP_ACTIVEMQ_VER: eap_activemq,
            JBOSS_FUSE_ON_EAP_CAMEL_VER: eap_camel,
            JBOSS_FUSE_ON_EAP_CXF_VER: eap_cxf,
        }
        raw_facts = generate_raw_fact_members(raw_facts_dict)
        product_dict[PRESENCE_KEY] = Product.PRESENT
        versions = []
        if fuse_versions:
            for version_data in fuse_versions:
                unknown_release = "Unknown-Release: " + version_data
                versions.append(FUSE_CLASSIFICATIONS.get(version_data, unknown_release))
            if versions:
                product_dict[VERSION_KEY] = versions
    elif systemctl_files or chkconfig:
        raw_facts_dict = {
            JBOSS_FUSE_SYSTEMCTL_FILES: systemctl_files,
            JBOSS_FUSE_CHKCONFIG: chkconfig,
        }
        raw_facts = generate_raw_fact_members(raw_facts_dict)
        product_dict[PRESENCE_KEY] = Product.POTENTIAL
    elif product_entitlement_found(subman_consumed, PRODUCT):
        raw_facts = SUBMAN_CONSUMED
        product_dict[PRESENCE_KEY] = Product.POTENTIAL
    elif product_entitlement_found(entitlements, PRODUCT):
        raw_facts = ENTITLEMENTS
        product_dict[PRESENCE_KEY] = Product.POTENTIAL
    else:
        product_dict[PRESENCE_KEY] = Product.ABSENT

    metadata[RAW_FACT_KEY] = raw_facts
    product_dict[META_DATA_KEY] = metadata
    return product_dict
