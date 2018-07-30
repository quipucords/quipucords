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

"""Ingests raw facts to determine the status of JBoss Web Server on system."""

from api.models import Product

from fingerprinter.utils import product_entitlement_found

PRODUCT = 'JBoss Web Server'
PRESENCE_KEY = 'presence'
VERSION_KEY = 'version'
RAW_FACT_KEY = 'raw_fact_key'
META_DATA_KEY = 'metadata'
SUBMAN_CONSUMED = 'subman_consumed'

JWS_CLASSIFICATIONS = {
    # Versions below 3.0.0 referred to as EWS, above are referred to as JWS
    # Version component information: https://access.redhat.com/articles/111723
    'Apache/2.2.10 (Unix)Apache Tomcat/5.5.23': 'EWS 1.0.0',
    'Apache/2.2.14 (Unix)Apache Tomcat/5.5.28': 'EWS 1.0.1',
    'Apache/2.2.17 (Unix)Apache Tomcat/5.5.33': 'EWS 1.0.2',
    'Apache/2.2.22 (Unix)Apache Tomcat/6.0.35': 'EWS 2.0.0',
    'Apache/2.2.22 (Unix)Apache Tomcat/6.0.37': 'EWS 2.0.1',
    'Apache/2.2.26 (Unix)Apache Tomcat/6.0.41': 'EWS 2.1.x',
    'JWS_3.0.1': 'JWS 3.0.1',
    'JWS_3.0.2': 'JWS 3.0.2',
    'JWS_3.0.3': 'JWS 3.0.3',
    'JWS_3.1.0': 'JWS 3.1.0',
    'Red Hat JBoss Web Server - Version 5.0.0 GA': 'JWS 5.0.0',
    'jws5': 'JWS 5.x.x',
}


def get_version(raw_versions):
    """Classify a version string.

    :param raw_versions: array of possible version strings
    """
    versions = []

    if raw_versions is not None:
        for version in raw_versions:
            # Turn the found version string into a standard format
            if version in JWS_CLASSIFICATIONS:
                versions.append(JWS_CLASSIFICATIONS[version])
    return versions


def detect_jboss_ws(source, facts):
    """Detect if JBoss Web Server is present based on system facts.

    :param source: The raw json source of the facts
    :param facts: facts for a system
    :returns: dictionary defining the product presence
    """
    product_dict = {'name': PRODUCT}
    product_dict[PRESENCE_KEY] = Product.ABSENT

    metadata = {
        'server_id': source['server_id'],
        'source_name': source['source_name'],
        'source_type': source['source_type'],
    }
    product_dict[META_DATA_KEY] = metadata
    subman_consumed = facts.get(SUBMAN_CONSUMED, [])
    version = get_version(facts.get('jws_version'))
    product_dict[VERSION_KEY] = version

    if facts.get('jws_installed_with_rpm'):
        product_dict[PRESENCE_KEY] = Product.PRESENT
    # Versions 3.0.0 and over explicitely mention 'JWS' in version string
    elif version:
        for ver in version:
            if 'EWS' not in ver:
                product_dict[PRESENCE_KEY] = Product.PRESENT
                break
    # Versions prior to 3.0.0 can only be detected by the presence of certain
    # EWS components and don't guarantee the installation of EWS
            else:
                product_dict[PRESENCE_KEY] = Product.POTENTIAL
    # System is subscribed to jws repo, but may or may not have it installed
    elif product_entitlement_found(subman_consumed, PRODUCT):
        product_dict[PRESENCE_KEY] = Product.POTENTIAL
    # If JWS not installed with rpm, detect potential presence by the presence
    # of a JBossEULA file or tomcat server in JWS_HOME directory
    elif facts.get('tomcat_is_part_of_redhat_product') or \
            facts.get('jws_has_eula_txt_file'):
        product_dict[PRESENCE_KEY] = Product.POTENTIAL

    return product_dict
