"""Ingests raw facts to determine the status of JBoss BRMS for a system."""

import itertools
import logging

from api.models import Product
from fingerprinter.constants import META_DATA_KEY, PRESENCE_KEY
from fingerprinter.utils import generate_raw_fact_members, product_entitlement_found
from utils import default_getter

logger = logging.getLogger(__name__)

PRODUCT = "JBoss BRMS"
VERSION_KEY = "version"
RAW_FACT_KEY = "raw_fact_key"
JBOSS_BRMS_MANIFEST_MF = "jboss_brms_manifest_mf"
JBOSS_BRMS_KIE_IN_BC = "jboss_brms_kie_in_business_central"
JBOSS_BRMS_LOCATE_KIE_API = "jboss_brms_locate_kie_api"
JBOSS_BRMS_KIE_API_VER = "jboss_brms_kie_api_ver"
JBOSS_BRMS_KIE_WAR_VER = "jboss_brms_kie_war_ver"
JBOSS_BRMS_DROOLS_CORE_VER = "jboss_brms_drools_core_ver"
SUBMAN_CONSUMED = "subman_consumed"
ENTITLEMENTS = "entitlements"

# These classifications apply to both strings in kie filenames and
# Implementation-Version strings in BRMS MANIFEST.MF files.
BRMS_CLASSIFICATIONS = {
    "7.5.0.Final-redhat-4": "RHDM 7.0.0",
    "6.5.0.Final-redhat-2": "BRMS 6.4.0",
    "6.4.0.Final-redhat-3": "BRMS 6.3.0",
    "6.3.0.Final-redhat-5": "BRMS 6.2.0",
    "6.2.0.Final-redhat-4": "BRMS 6.1.0",
    "6.0.3-redhat-6": "BRMS 6.0.3",
    "6.0.3-redhat-4": "BRMS 6.0.2",
    "6.0.2-redhat-6": "BRMS 6.0.1",
    "6.0.2-redhat-2": "BRMS 6.0.0",
    "5.3.1.BRMS": "BRMS 5.3.1",
    "5.3.0.BRMS": "BRMS 5.3.0",
    "5.2.0.BRMS": "BRMS 5.2.0",
    "5.1.0.BRMS": "BRMS 5.1.0",
    "5.0.2.BRMS": "BRMS 5.0.2",
    "5.0.1.BRMS": "BRMS 5.0.1",
    "5.0.1": "Drools 5.0.1",
    "5.6.0.Final": "Drools 5.6.0",
    "6.0.1.Final": "Drools 6.0.1",
    "6.5.0.Final": "Drools 6.5.0",
    "7.0.0.Final": "Drools 7.0.0",
    "7.5.0.Final": "Drools 7.5.0",
    "7.6.0.Final": "Drools 7.6.0",
}


def classify_version_string(version_string):
    """Classify a version string.

    :param version_string: a BRMS version string, in MANIFEST.MF format.

    :returns: a version string in our standard format.
    """
    if version_string in BRMS_CLASSIFICATIONS:
        return BRMS_CLASSIFICATIONS[version_string]

    if "redhat" in version_string:
        return "Unknown-Release: " + version_string

    return None


def detect_jboss_brms(source, facts):
    """Detect if JBoss BRMS is present based on system facts.

    :param source: The source of the facts
    :param facts: facts for a system
    :returns: dictionary defining the product presence
    """
    manifest_mfs = default_getter(facts, JBOSS_BRMS_MANIFEST_MF, set())
    kie_in_bc = default_getter(facts, JBOSS_BRMS_KIE_IN_BC, set())
    locate_kie_api = default_getter(facts, JBOSS_BRMS_LOCATE_KIE_API, set())
    find_kie_api = default_getter(facts, JBOSS_BRMS_KIE_API_VER, set())
    find_kie_war = default_getter(facts, JBOSS_BRMS_KIE_WAR_VER, set())
    find_drools = default_getter(facts, JBOSS_BRMS_DROOLS_CORE_VER, set())
    subman_consumed = default_getter(facts, SUBMAN_CONSUMED, [])
    entitlements = default_getter(facts, ENTITLEMENTS, [])

    metadata = {
        "server_id": source["server_id"],
        "source_name": source["source_name"],
        "source_type": source["source_type"],
    }
    product_dict = {"name": PRODUCT}

    versions = set()
    found_kie_version = False
    for _, version_string in itertools.chain(kie_in_bc, locate_kie_api):
        category = classify_version_string(version_string)
        # categories that are falsey are not Red Hat files.
        if category:
            versions.add(category)
            found_kie_version = True

    found_manifest_version = False
    for _, manifest_version in manifest_mfs:
        category = classify_version_string(manifest_version)
        if category:
            versions.add(category)
            found_manifest_version = True

    for _, filename in itertools.chain(find_kie_api, find_drools):
        category = classify_version_string(filename)
        if category:
            versions.add(category)

    for search_version in find_kie_war:
        category = classify_version_string(search_version)
        if category:
            versions.add(category)

    # Exclude Drools versions for now.
    found_redhat_brms = any((not version.startswith("Drools") for version in versions))

    if found_redhat_brms:
        raw_facts_dict = {
            JBOSS_BRMS_MANIFEST_MF: found_manifest_version,
            JBOSS_BRMS_KIE_IN_BC: (found_kie_version and kie_in_bc),
            JBOSS_BRMS_LOCATE_KIE_API: (found_kie_version and locate_kie_api),
            JBOSS_BRMS_KIE_API_VER: find_kie_api,
            JBOSS_BRMS_KIE_WAR_VER: find_kie_war,
            JBOSS_BRMS_DROOLS_CORE_VER: find_drools,
        }
        raw_facts = generate_raw_fact_members(raw_facts_dict)
        metadata[RAW_FACT_KEY] = raw_facts
        product_dict[PRESENCE_KEY] = Product.PRESENT
        product_dict[VERSION_KEY] = list(versions)

    elif product_entitlement_found(subman_consumed, PRODUCT):
        metadata[RAW_FACT_KEY] = SUBMAN_CONSUMED
        product_dict[PRESENCE_KEY] = Product.POTENTIAL
    elif product_entitlement_found(entitlements, PRODUCT):
        metadata[RAW_FACT_KEY] = ENTITLEMENTS
        product_dict[PRESENCE_KEY] = Product.POTENTIAL
    else:
        metadata[RAW_FACT_KEY] = None
        product_dict[PRESENCE_KEY] = Product.ABSENT

    product_dict[META_DATA_KEY] = metadata
    return product_dict
