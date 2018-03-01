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
from fingerprinter.utils import (product_entitlement_found,
                                 generate_raw_fact_members)

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

PRODUCT = 'JBoss EAP'
PRESENCE_KEY = 'presence'
VERSION_KEY = 'version'
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
    eap_jar_versions = facts.get(JBOSS_EAP_JAR_VER, [])
    eap_run_jar_versions = facts.get(JBOSS_EAP_RUN_JAR_VER, [])
    subman_consumed = facts.get(SUBMAN_CONSUMED, [])
    entitlements = facts.get(ENTITLEMENTS, [])
    eap_jar_versions += eap_run_jar_versions

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
    raw_facts = None
    if (running_paths or
            packages or
            modules_jar or
            eap_home or
            eap_jar_versions):
        raw_facts_dict = {JBOSS_EAP_RUNNING_PATHS: running_paths,
                          JBOSS_EAP_PACKAGES: packages,
                          JBOSS_EAP_LOCATE_JBOSS_MODULES_JAR: modules_jar,
                          JBOSS_EAP_EAP_HOME: eap_home,
                          JBOSS_EAP_JAR_VER: eap_jar_versions,
                          JBOSS_EAP_RUN_JAR_VER: eap_run_jar_versions}
        raw_facts = generate_raw_fact_members(raw_facts_dict)
        product_dict[PRESENCE_KEY] = Product.PRESENT
        if eap_jar_versions:
            versions = []
            for version_data in eap_jar_versions:
                version = version_data.get(VERSION_KEY)
                unknown_release = 'Unknown-Release: ' + version
                versions.append(EAP_CLASSIFICATIONS.get(version,
                                                        unknown_release))
                if versions != []:
                    version_set = set(versions)
                    product_dict[VERSION_KEY] = list(version_set)
    elif (jboss_user or
          common_files or
          eap_processes or
          systemctl_files or
          chkconfig):
        raw_facts_dict = {JBOSS_EAP_JBOSS_USER: jboss_user,
                          JBOSS_EAP_COMMON_FILES: common_files,
                          JBOSS_EAP_PROCESSES: eap_processes,
                          JBOSS_EAP_SYSTEMCTL_FILES: systemctl_files,
                          JBOSS_EAP_CHKCONFIG: chkconfig}
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
