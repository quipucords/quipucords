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

import logging

from api.models import Product

from fingerprinter.utils import product_entitlement_found

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

PRODUCT = 'JBoss Web Server'
PRESENCE_KEY = 'presence'
VERSION_KEY = 'version'
RAW_FACT_KEY = 'raw_fact_key'
META_DATA_KEY = 'metadata'
SUBMAN_CONSUMED = 'subman_consumed'

JWS_CLASSIFICATIONS = {
    # Versions below 3.0.0 referred to as EWS, above referred to as JWS
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
    'Server version: Apache/2.4.6 (Red Hat)': 'JWS 3.0.3',
    'JWS_3.1.0': 'JWS 3.1.0',
    'Red Hat JBoss Web Server - Version 5.0.0 GA': 'JWS 5.0.0',
    'jws5': 'JWS 5.x.x',
}


def get_version(rawjson):
    """Classify a version string.

    :param rawjson: raw json of results from ansible query of possible versions
    """
    versions = []

    if rawjson is not None:
        results = rawjson['results']

        for i in range(0, len(results)):
            num_versions = len(results[i]['stdout_lines'])
            if num_versions > 0:
                version = results[i]['stdout_lines'][0]
                # Turn the found version string into a standard format
                if version in JWS_CLASSIFICATIONS:
                    versions.append(JWS_CLASSIFICATIONS[version])
    return versions


def installed_with_rpm(stdout):
    """Determine if jws was installed with rpm. Version 3 and up.

    :param stdout: array of installed groups as result of command
    'yum grouplist jws...'
    """
    # it matters not if there are multiple versions installed with rpm. Param
    # stdout only lists zero or one installed jws group
    if stdout is not None and len(stdout) == 1 and 'Red Hat JBoss Web Server' \
       in stdout[0]:
        return True
    return False


def has_jboss_eula_file(jboss_eula_location):
    """Check if JBossEULA.txt exists in JWS_Home directory.

    :param jboss_eula_location: Result of $(ls $JWS_HOME/JBossEULA.txt)
    """
    if jboss_eula_location is not None and 'No such file or directory' not in \
       jboss_eula_location:
        return True
    return False


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
    product_dict[VERSION_KEY] = get_version(facts.get('jws_version'))

    subman_consumed = facts.get(SUBMAN_CONSUMED, [])

    if installed_with_rpm(facts.get('installed_with_rpm')):
        product_dict[PRESENCE_KEY] = Product.PRESENT
    elif product_entitlement_found(subman_consumed, PRODUCT):
        product_dict[PRESENCE_KEY] = Product.POTENTIAL
    # If JWS not installed with rpm, detect a potential presence by the
    # presence of a JBossEULA file or tomcat server in JWS_HOME
    elif facts.get('tomcat_is_part_of_redhat_product') is True or \
            has_jboss_eula_file(facts.get('jboss_eula_location')):

        product_dict[PRESENCE_KEY] = Product.POTENTIAL

    return product_dict
