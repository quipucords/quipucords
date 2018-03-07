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
PRESENCE = 'presence'
VERSION = 'version'
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
JBOSS_EAP_JAR_VER = 'jboss_eap_jar_ver'
JBOSS_EAP_RUN_JAR_VER = 'jboss_eap_run_jar_ver'
EAP5_HOME_VERSION_TXT = 'eap5_home_version_txt'
EAP5_HOME_README_HTML = 'eap5_home_readme_html'
EAP5_HOME_RUN_JAR_MANIFEST = 'eap5_home_run_jar_manifest'
SUBMAN_CONSUMED = 'subman_consumed'
ENTITLEMENTS = 'entitlements'

EAP_CLASSIFICATIONS = {
    'JBoss_4_0_0': 'JBossAS-4',
    'JBoss_4_0_1_SP1': 'JBossAS-4',
    'JBoss_4_0_2': 'JBossAS-4',
    'JBoss_4_0_3_SP1': 'JBossAS-4',
    'JBoss_4_0_4_GA': 'JBossAS-4',
    'Branch_4_0': 'JBossAS-4',
    'JBoss_4_2_0_GA': 'JBossAS-4',
    'JBoss_4_2_1_GA': 'JBossAS-4',
    'JBoss_4_2_2_GA': 'JBossAS-4',
    'JBoss_4_2_3_GA': 'JBossAS-4',
    'JBoss_5_0_0_GA': 'JBossAS-5',
    'JBoss_5_0_1_GA': 'JBossAS-5',
    'JBoss_5_1_0_GA': 'JBossAS-5',
    'JBoss_6.0.0.Final': 'JBossAS-6',
    'JBoss_6.1.0.Final': 'JBossAS-6',
    '1.0.1.GA': 'JBossAS-7',
    '1.0.2.GA': 'JBossAS-7',
    '1.1.1.GA': 'JBossAS-7',
    '1.2.0.CR1': 'JBossAS-7',
    '1.2.0.Final': 'WildFly-8',
    '1.2.2.Final': 'WildFly-8',
    '1.2.4.Final': 'WildFly-8',
    '1.3.0.Beta3': 'WildFly-8',
    '1.3.0.Final': 'WildFly-8',
    '1.3.3.Final': 'WildFly-8',
    '1.3.4.Final': 'WildFly-9',
    '1.4.2.Final': 'WildFly-9',
    '1.4.3.Final': 'WildFly-9',
    '1.4.4.Final': 'WildFly-10',
    '1.5.0.Final': 'WildFly-10',
    '1.5.1.Final': 'WildFly-10',
    '1.5.2.Final': 'WildFly-10',
    'JBPAPP_4_2_0_GA': 'EAP-4.2',
    'JBPAPP_4_2_0_GA_C': 'EAP-4.2',
    'JBPAPP_4_3_0_GA': 'EAP-4.3',
    'JBPAPP_4_3_0_GA_C': 'EAP-4.3',
    'JBPAPP_5_0_0_GA': 'EAP-5.0.0',
    'JBPAPP_5_0_1': 'EAP-5.0.1',
    'JBPAPP_5_1_0': 'EAP-5.1.0',
    'JBPAPP_5_1_1': 'EAP-5.1.1',
    'JBPAPP_5_1_2': 'EAP-5.1.2',
    'JBPAPP_5_2_0': 'EAP-5.2.0',
    '1.1.2.GA-redhat-1': 'EAP-6.0.0',
    '1.1.3.GA-redhat-1': 'EAP-6.0.1',
    '1.2.0.Final-redhat-1': 'EAP-6.1.0',
    '1.2.2.Final-redhat-1': 'EAP-6.1.1',
    '1.3.0.Final-redhat-2': 'EAP-6.2',
    '1.3.3.Final-redhat-1': 'EAP-6.3',
    '1.3.4.Final-redhat-1': 'EAP-6.3',
    '1.3.5.Final-redhat-1': 'EAP-6.3',
    '1.3.6.Final-redhat-1': 'EAP-6.4',
    '1.3.7.Final-redhat-1': 'EAP-6.4',
    '1.4.4.Final-redhat-1': 'EAP-7.0',
    '1.5.1.Final-redhat-1': 'EAP-7.0',
    '1.5.4.Final-redhat-1': 'EAP-7.0'
}


def classify_jar_versions(jar_versions):
    """Classify raw jar versions.

    :param jar_versions: an iterable of EAP jar version tuples.
    :returns: a set of classifications, or Unknown-Release for unknown strings.
    """
    versions = set()

    if not jar_versions:
        return versions

    for version_data in jar_versions:
        version = version_data.get(VERSION)
        unknown_release = 'Unknown-Release: ' + version
        versions.add(EAP_CLASSIFICATIONS.get(version,
                                             unknown_release))
    return versions


def versions_eap_presence(jar_versions):
    """Test whether jar_versions includes an EAP version."""
    if not jar_versions:
        return Product.UNKNOWN

    for version in jar_versions.values():
        if EAP_CLASSIFICATIONS.get(version, '').startswith('EAP'):
            return Product.PRESENT

    return Product.UNKNOWN


# classify_versions is different than classify_jar_versions above
# because the jar_versions expects a list of dictionaries with keys
# 'version' and 'date', whereas this just expects a list of version
# strings.
def classify_versions(versions):
    """Classify the version strings in versions."""
    classes = set()

    for version in versions.values():
        if version in EAP_CLASSIFICATIONS:
            classes.add(EAP_CLASSIFICATIONS[version])
        else:
            classes.add('Unknown-Release: ' + version)

    return classes


def find_eap_entitlement(entitlements):
    """Look for JBoss EAP entitlements in a dict of entitlements."""
    if not entitlements:
        return Product.ABSENT

    if product_entitlement_found(entitlements, PRODUCT):
        return Product.POTENTIAL

    return Product.UNKNOWN


# Each fact can tell us the presence, version, or both of
# EAP. (Version without presence happens when we detect Wildfly. That
# leads to PRESENCE False and Version 'Wildfly-10' or something like
# that.) For each fact, PRESENCE and VERSION are functions that are
# applied to the fact's value and return presence or version
# information respectively. PRESENCE can also be a literal presence
# value and VERSION can be a literal set, as a convenience.
FACTS = {
    JBOSS_EAP_RUNNING_PATHS: {PRESENCE: Product.PRESENT},
    JBOSS_EAP_JBOSS_USER: {PRESENCE: Product.POTENTIAL},
    JBOSS_EAP_COMMON_FILES: {PRESENCE: Product.POTENTIAL},
    JBOSS_EAP_PROCESSES: {PRESENCE: Product.POTENTIAL},
    JBOSS_EAP_PACKAGES: {PRESENCE: Product.PRESENT},
    JBOSS_EAP_LOCATE_JBOSS_MODULES_JAR: {PRESENCE: Product.PRESENT},
    JBOSS_EAP_SYSTEMCTL_FILES: {PRESENCE: Product.POTENTIAL},
    JBOSS_EAP_CHKCONFIG: {PRESENCE: Product.POTENTIAL},
    JBOSS_EAP_EAP_HOME: {PRESENCE: Product.PRESENT},
    JBOSS_EAP_JAR_VER: {
        PRESENCE: Product.PRESENT,
        VERSION: classify_jar_versions},
    JBOSS_EAP_RUN_JAR_VER: {
        PRESENCE: Product.PRESENT,
        VERSION: classify_jar_versions},
    EAP5_HOME_VERSION_TXT: {PRESENCE: Product.PRESENT},
    EAP5_HOME_README_HTML: {PRESENCE: Product.PRESENT},
    EAP5_HOME_RUN_JAR_MANIFEST: {
        PRESENCE: versions_eap_presence,
        VERSION: classify_versions},
    SUBMAN_CONSUMED: {PRESENCE: find_eap_entitlement},
    ENTITLEMENTS: {PRESENCE: find_eap_entitlement}
}


def call_or_value(obj, argument):
    """Either call a function or return a literal value."""
    if callable(obj):
        return obj(argument)

    return obj


PRESENCE_ORDER = [Product.UNKNOWN, Product.ABSENT,
                  Product.POTENTIAL, Product.PRESENT]


# pylint: disable=invalid-name
def presence_ge(a, b):
    """Compare two presence values, like >= for numbers.

    :returns: True if a is as or more "sure" of presence than b, False if not.
    """
    return PRESENCE_ORDER.index(a) >= PRESENCE_ORDER.index(b)


def detect_jboss_eap(source, facts):
    """Detect if JBoss EAP is present based on system facts.

    :param source: The source of the facts
    :param facts: facts for a system
    :returns: dictionary defining the product presence
    """
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

    presence = Product.ABSENT  # Default to ABSENT to match previous behavior.
    versions = set()  # Set of EAP or WildFly versions present.
    raw_facts = []  # List of facts that contributed to presence.

    for fact, actions in FACTS.items():
        fact_value = facts.get(fact)
        if not fact_value:
            continue
        if PRESENCE in actions:
            new_presence = call_or_value(actions[PRESENCE], fact_value)
            if not presence_ge(presence, new_presence):
                # presence is being upgraded. Replace old presence
                # with new presence, and adjust raw facts list.
                presence = new_presence
                raw_facts = [fact]
            elif presence == new_presence and presence != Product.UNKNOWN:
                # presence matches, which means facts is more evidence
                # in support of our current presence value.
                raw_facts.append(fact)
            # If fact only supports a less-sure conclusion than the
            # one we already have, then we ignore it.
        if VERSION in actions:
            new_versions = call_or_value(actions[VERSION], fact_value)
            versions.update(new_versions)

    product_dict[PRESENCE] = presence
    if versions:
        product_dict[VERSION] = list(versions)

    if raw_facts:
        metadata[RAW_FACT_KEY] = '/'.join(raw_facts)
    else:
        metadata[RAW_FACT_KEY] = None

    product_dict[META_DATA_KEY] = metadata

    return product_dict
