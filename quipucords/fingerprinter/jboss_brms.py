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

"""Ingests raw facts to determine the status of JBoss BRMS for a system."""

import os
import logging
from api.models import Product, Source
from fingerprinter.utils import (strip_prefix,
                                 strip_suffix,
                                 product_entitlement_found,
                                 generate_raw_fact_members)

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

PRODUCT = 'JBoss BRMS'
PRESENCE_KEY = 'presence'
RAW_FACT_KEY = 'raw_fact_key'
META_DATA_KEY = 'metadata'
BUSINESS_CENTRAL_CANDIDATES = 'business_central_candidates'
KIE_SERVER_CANDIDATES = 'kie_server_candidates'
JBOSS_BRMS_MANIFEST_MF = 'jboss_brms_manifest_mf'
JBOSS_BRMS_KIE_IN_BC = 'jboss_brms_kie_in_business_central'
JBOSS_BRMS_LOCATE_KIE_API = 'jboss_brms_locate_kie_api'
SUBMAN_CONSUMED = 'subman_consumed'
ENTITLEMENTS = 'entitlements'

BRMS_CLASSIFICATIONS = {
    '6.4.0.Final-redhat-3': 'BRMS 6.3.0',
    '6.3.0.Final-redhat-5': 'BRMS 6.2.0',
    '6.2.0.Final-redhat-4': 'BRMS 6.1.0',
    '6.0.3-redhat-6': 'BRMS 6.0.3',
    '6.0.3-redhat-4': 'BRMS 6.0.2',
    '6.0.2-redhat-6': 'BRMS 6.0.1',
    '6.0.2-redhat-2': 'BRMS 6.0.0',
    '5.3.1.BRMS': 'BRMS 5.3.1',
    '5.3.0.BRMS': 'BRMS 5.3.0',
    '5.2.0.BRMS': 'BRMS 5.2.0',
    '5.1.0.BRMS': 'BRMS 5.1.0',
    '5.0.2.BRMS': 'BRMS 5.0.2',
    '5.0.1.BRMS': 'BRMS 5.0.1',
    'drools-core-5.0.0': 'BRMS 5.0.0',
    '6.5.0.Final': 'Drools 6.5.0'
}


def classify_kie_file(pathname):
    """Classify a kie-api-* file.

    :param pathname: the path to the file
    :returns: a BRMS version string, or None if not a Red Hat kie file.
    """
    # os.path.basename behaves differently if the last part of the
    # path ends in a /, so normalize.
    if pathname.endswith('/'):
        pathname = pathname[:-1]

    basename = os.path.basename(pathname)

    version_string = strip_suffix(
        strip_prefix(basename, 'kie-api-'),
        '.jar')

    if version_string in BRMS_CLASSIFICATIONS:
        return BRMS_CLASSIFICATIONS[version_string]

    if 'redhat' in version_string:
        return version_string

    return None


# pylint: disable=too-many-locals
def detect_jboss_brms(source, facts):
    """Detect if JBoss BRMS is present based on system facts.

    :param source: The source of the facts
    :param facts: facts for a system
    :returns: dictionary defining the product presence
    """
    business_central_candidates = facts.get(BUSINESS_CENTRAL_CANDIDATES, [])
    kie_server_candidates = facts.get(KIE_SERVER_CANDIDATES, [])
    manifest_mfs = facts.get(JBOSS_BRMS_MANIFEST_MF, {})
    kie_in_bc = facts.get(JBOSS_BRMS_KIE_IN_BC, [])
    locate_kie_api = facts.get(JBOSS_BRMS_LOCATE_KIE_API, [])
    subman_consumed = facts.get(SUBMAN_CONSUMED, [])
    entitlements = facts.get(ENTITLEMENTS, [])
    base_directories = set(business_central_candidates + kie_server_candidates)
    kie_files = kie_in_bc + locate_kie_api

    kie_versions_by_directory = {}
    for directory in base_directories:
        versions_in_dir = set()
        for filename in list(kie_files):
            if filename.startswith(directory):
                kie_files.remove(filename)
                category = classify_kie_file(filename)
                if category:
                    versions_in_dir.add(category)
                # Deliberately drop files if their category is falsey,
                # because it means that they are not Red Hat files.
        kie_versions_by_directory[directory] = versions_in_dir

    found_manifest = any(('Red Hat' in manifest
                          for _, manifest in manifest_mfs.items()))
    found_versions = any((version
                          for _, version in kie_versions_by_directory.items()))
    found_redhat_brms = (found_manifest or found_versions)

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

    if found_redhat_brms:
        raw_facts_dict = {JBOSS_BRMS_MANIFEST_MF: found_manifest,
                          JBOSS_BRMS_KIE_IN_BC: (found_versions and kie_in_bc),
                          JBOSS_BRMS_LOCATE_KIE_API: (found_versions and
                                                      locate_kie_api)}
        raw_facts = generate_raw_fact_members(raw_facts_dict)
        metadata[RAW_FACT_KEY] = raw_facts
        product_dict[PRESENCE_KEY] = Product.PRESENT
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
