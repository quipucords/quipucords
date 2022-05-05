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

import bisect
import logging

from api.models import Product
from fingerprinter.constants import META_DATA_KEY
from fingerprinter.utils import product_entitlement_found

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

NAME = 'name'
PRODUCT = 'JBoss EAP'
PRESENCE = 'presence'
VERSION = 'version'
RAW_FACT_KEY = 'raw_fact_key'
JBOSS_EAP_RUNNING_PATHS = 'jboss_eap_running_paths'
JBOSS_EAP_JBOSS_USER = 'jboss_eap_id_jboss'
JBOSS_EAP_COMMON_FILES = 'jboss_eap_common_files'
JBOSS_PROCESSES = 'jboss_processes'
JBOSS_EAP_PACKAGES = 'jboss_eap_packages'
JBOSS_EAP_LOCATE_JBOSS_MODULES_JAR = 'jboss_eap_locate_jboss_modules_jar'
JBOSS_EAP_SYSTEMCTL_FILES = 'jboss_eap_systemctl_unit_files'
JBOSS_EAP_CHKCONFIG = 'jboss_eap_chkconfig'
JBOSS_EAP_EAP_HOME = 'eap_home_ls'
JBOSS_EAP_JAR_VER = 'jboss_eap_jar_ver'
JBOSS_EAP_RUN_JAR_VER = 'jboss_eap_run_jar_ver'
EAP_HOME_VERSION_TXT = 'eap_home_version_txt'
EAP_HOME_README_TXT = 'eap_home_readme_txt'
EAP_HOME_MODULES_MANIFEST = 'eap_home_jboss_modules_manifest'
EAP_HOME_MODULES_VERSION = 'eap_home_jboss_modules_version'
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
    '1.6.0.Final': 'WildFly-11',
    '1.6.1.Final': 'WildFly-11',
    '1.7.0.Final': 'WildFly-12',
    'JBPAPP_4_2_0_GA': '4.2',
    'JBPAPP_4_2_0_GA_C': '4.2',
    'JBPAPP_4_3_0_GA': '4.3',
    'JBPAPP_4_3_0_GA_C': '4.3',
    'JBPAPP_5_0_0_GA': '5.0.0',
    'JBPAPP_5_0_1': '5.0.1',
    'JBPAPP_5_1_0': '5.1.0',
    'JBPAPP_5_1_1': '5.1.1',
    'JBPAPP_5_1_2': '5.1.2',
    'JBPAPP_5_2_0': '5.2.0',
    '1.1.2.GA-redhat-1': '6.0.0',
    '1.1.3.GA-redhat-1': '6.0.1',
    '1.2.0.Final-redhat-1': '6.1.0',
    '1.2.2.Final-redhat-1': '6.1.1',
    '1.3.0.Final-redhat-2': '6.2.0',
    '1.3.3.Final-redhat-1': '6.3.0',
    '1.3.4.Final-redhat-1': '6.3',
    '1.3.5.Final-redhat-1': '6.3',
    '1.3.6.Final-redhat-1': '6.4.0',
    '1.3.7.Final-redhat-1': '6.4',
    '1.4.4.Final-redhat-1': '7.0',
    '1.5.1.Final-redhat-1': '7.0.0',
    '1.5.4.Final-redhat-1': '7.0',
    '1.6.0.Final-redhat-1': '7.1.0',
    '1.8.6.Final-redhat-00001': '7.2.0',
    '1.9.1.Final-redhat-00001': '7.3.0'
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


def any_value_true(obj):
    """Check whether any value in a dictionary is true."""
    if any(obj.values()):
        return Product.PRESENT

    return Product.ABSENT


def process_version_txt(version_dict):
    """Get the EAP version from a version.txt string."""
    versions = set()
    for _, version in version_dict.items():
        if version:
            versions.add(version.strip())

    return versions


IMPLEMENTATION_VERSION = 'Implementation-Version:'


def verify_classification(classification):
    """Check whether a classification is EAP vs Wildfly or JBossAS."""
    if 'wildfly' in classification.lower() or \
            'jbossas' in classification.lower():
        return False
    return True


def is_eap_manifest_version(manifest_dict):
    """Check whether a manifest contains an EAP version string or not."""
    for _, manifest in manifest_dict.items():
        if isinstance(manifest, str):
            for line in manifest.splitlines():
                if IMPLEMENTATION_VERSION in line:
                    _, _, ver = line.partition(IMPLEMENTATION_VERSION)
                    classification = EAP_CLASSIFICATIONS.get(ver.strip())
                    if classification and \
                            verify_classification(classification):
                        return Product.PRESENT
        else:
            logger.warning('Expected a dictionary of strings for %s, '
                           'but found %s.  Invalid value: %s',
                           EAP_HOME_MODULES_VERSION, type(manifest), manifest)
    return Product.ABSENT


def get_eap_manifest_version(manifest_dict):
    """Get the EAP version from a MANIFEST.MF string."""
    versions = set()
    for _, manifest in manifest_dict.items():
        if isinstance(manifest, str):
            for line in manifest.splitlines():
                if IMPLEMENTATION_VERSION in line:
                    _, _, ver = line.partition(IMPLEMENTATION_VERSION)
                    classification = EAP_CLASSIFICATIONS.get(ver.strip())
                    if classification:
                        versions.add(classification)
        else:
            logger.warning('Expected a dictionary of strings for %s, '
                           'but found %s.  Invalid value: %s',
                           EAP_HOME_MODULES_VERSION, type(manifest), manifest)

    return versions


def is_eap_jar_version(version_dict):
    """Check whether a 'jar -version' string contains an EAP version string."""
    for _, version in version_dict.items():
        if isinstance(version, str):
            _, _, rest = version.partition('version')
            classification = EAP_CLASSIFICATIONS.get(rest.strip())
            if classification and verify_classification(classification):
                return Product.PRESENT
        else:
            logger.warning('Expected a dictionary of strings for %s, '
                           'but found %s.  Invalid value: %s',
                           JBOSS_EAP_JAR_VER, type(version), version)
    return Product.ABSENT


def get_eap_jar_version(version_dict):
    """Get the EAP version from a 'jar -version' string."""
    versions = set()
    for _, version in version_dict.items():
        if isinstance(version, str):
            _, _, rest = version.partition('version')
            classification = EAP_CLASSIFICATIONS.get(rest.strip())
            if classification:
                versions.add(classification)
        else:
            logger.warning('Expected a dictionary of strings for %s, '
                           'but found %s.  Invalid value: %s',
                           JBOSS_EAP_JAR_VER, type(version), version)

    return versions


# Each fact can tell us the presence, version, or both of
# EAP. (Version without presence happens when we detect Wildfly. That
# leads to PRESENCE False and Version 'Wildfly-10' or something like
# that.) For each fact, PRESENCE and VERSION are functions that are
# applied to the fact's value and return presence or version
# information respectively. PRESENCE can also be a literal presence
# value and VERSION can be a literal set, as a convenience.
FACTS = [
    {NAME: JBOSS_EAP_RUNNING_PATHS, PRESENCE: Product.POTENTIAL},
    {NAME: JBOSS_EAP_JBOSS_USER, PRESENCE: Product.POTENTIAL},
    {NAME: JBOSS_EAP_COMMON_FILES, PRESENCE: Product.POTENTIAL},
    {NAME: JBOSS_PROCESSES, PRESENCE: Product.POTENTIAL},
    {NAME: JBOSS_EAP_PACKAGES, PRESENCE: Product.PRESENT},
    {NAME: JBOSS_EAP_LOCATE_JBOSS_MODULES_JAR, PRESENCE: Product.POTENTIAL},
    {NAME: JBOSS_EAP_SYSTEMCTL_FILES, PRESENCE: Product.POTENTIAL},
    {NAME: JBOSS_EAP_CHKCONFIG, PRESENCE: Product.POTENTIAL},
    {NAME: JBOSS_EAP_EAP_HOME,
     PRESENCE: any_value_true},
    {NAME: JBOSS_EAP_JAR_VER,
     PRESENCE: Product.PRESENT,
     VERSION: classify_jar_versions},
    {NAME: JBOSS_EAP_RUN_JAR_VER,
     PRESENCE: Product.PRESENT,
     VERSION: classify_jar_versions},
    {NAME: EAP_HOME_VERSION_TXT,
     PRESENCE: any_value_true,
     VERSION: process_version_txt},
    {NAME: EAP_HOME_README_TXT,
     PRESENCE: Product.ABSENT},
    {NAME: EAP_HOME_MODULES_MANIFEST,
     PRESENCE: is_eap_manifest_version,
     VERSION: get_eap_manifest_version},
    {NAME: EAP_HOME_MODULES_VERSION,
     PRESENCE: is_eap_jar_version,
     VERSION: get_eap_jar_version},
    {NAME: EAP5_HOME_VERSION_TXT, PRESENCE: any_value_true},
    {NAME: EAP5_HOME_README_HTML, PRESENCE: any_value_true},
    {NAME: EAP5_HOME_RUN_JAR_MANIFEST,
     PRESENCE: versions_eap_presence,
     VERSION: classify_versions},
    {NAME: SUBMAN_CONSUMED, PRESENCE: find_eap_entitlement},
    {NAME: ENTITLEMENTS, PRESENCE: find_eap_entitlement}
]


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


def version_aware_dedup(versions):
    """Deduplicate a list of version numbers of different precisions.

    If versions contains '7.0.0' and '7.0', this function will return
    a single entry for '7.0.0'.

    :param versions: an iterable of version strings
    :returns: a deduplicated set of version strings
    """
    in_order = sorted(versions)
    deduped = set()

    for version in in_order:
        i = bisect.bisect_right(in_order, version)
        # i is the first index in in_order after the index of
        # version. If there are entries in in_order that have version
        # as a prefix but are more specific, they should be
        # immediately to the right of version. Meaning that if there
        # is one at all, then there should be one at index i.
        if i < len(in_order) and in_order[i].startswith(version):
            continue
        deduped.add(version)

    return deduped


def detect_jboss_eap(source, facts):
    """Detect if JBoss EAP is present based on system facts.

    :param source: The source of the facts
    :param facts: facts for a system
    :returns: dictionary defining the product presence
    """
    metadata = {
        'server_id': source['server_id'],
        'source_name': source['source_name'],
        'source_type': source['source_type'],
    }
    product_dict = {'name': PRODUCT}

    presence = Product.ABSENT  # Default to ABSENT to match previous behavior.
    versions = set()  # Set of EAP or WildFly versions present.
    raw_facts = []  # List of facts that contributed to presence.

    for fact_dict in FACTS:
        fact = fact_dict[NAME]
        fact_value = facts.get(fact)
        if not fact_value:
            continue
        if PRESENCE in fact_dict:
            new_presence = call_or_value(fact_dict[PRESENCE], fact_value)
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
        if VERSION in fact_dict:
            new_versions = call_or_value(fact_dict[VERSION], fact_value)
            versions.update(new_versions)

    product_dict[PRESENCE] = presence
    if versions:
        versions = [
            version for version in versions
            if not version.lower().startswith('wildfly') and not
            version.lower().startswith('jbossas')]
        if not versions:
            product_dict[PRESENCE] = Product.ABSENT
        product_dict[VERSION] = list(version_aware_dedup(versions))

    if raw_facts:
        metadata[RAW_FACT_KEY] = '/'.join(raw_facts)
    else:
        metadata[RAW_FACT_KEY] = None

    product_dict[META_DATA_KEY] = metadata

    return product_dict
