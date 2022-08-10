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
from fingerprinter.constants import META_DATA_KEY, PRESENCE_KEY
from fingerprinter.utils import generate_raw_fact_members, product_entitlement_found

NAME = "name"
PRODUCT = "JBoss Web Server"
VERSION_KEY = "version"
RAW_FACT_KEY = "raw_fact_key"
SUBMAN_CONSUMED = "subman_consumed"

JWS_INSTALLED_WITH_RPM = "jws_installed_with_rpm"
JWS_HAS_EULA_TXT_FILE = "jws_has_eula_txt_file"
TOMCAT_PART_OF_REDHAT_PRODUCT = "tomcat_is_part_of_redhat_product"
JWS_VERSION = "jws_version"
JWS_HAS_CERT = "jws_has_cert"

JWS_CLASSIFICATIONS = {
    # Versions below 3.0.0 referred to as EWS, above are referred to as JWS
    # Version component information: https://access.redhat.com/articles/111723
    "Apache/2.2.10 (Unix)Apache Tomcat/5.5.23": "EWS 1.0.0",
    "Apache/2.2.14 (Unix)Apache Tomcat/5.5.28": "EWS 1.0.1",
    "Apache/2.2.17 (Unix)Apache Tomcat/5.5.33": "EWS 1.0.2",
    "Apache/2.2.22 (Unix)Apache Tomcat/6.0.35": "EWS 2.0.0",
    "Apache/2.2.22 (Unix)Apache Tomcat/6.0.37": "EWS 2.0.1",
    "Apache/2.2.26 (Unix)Apache Tomcat/6.0.41": "EWS 2.1.x",
    "JWS_3.0.1": "JWS 3.0.1",
    "JWS_3.0.2": "JWS 3.0.2",
    "JWS_3.0.3": "JWS 3.0.3",
    "JWS_3.1.0": "JWS 3.1.0",
    "JWS_3.1.1": "JWS 3.1.1",
    "JWS_3.1.2": "JWS 3.1.2",
    "JWS_3.1.3": "JWS 3.1.3",
    "JWS_3.1.4": "JWS 3.1.4",
    "JWS_3.1.5": "JWS 3.1.5",
    "JWS_3.1.6": "JWS 3.1.6",
    "JWS_3.1.7": "JWS 3.1.7",
    "JWS_3.1.8": "JWS 3.1.8",
    "JWS_3.1.9": "JWS 3.1.9",
    "Red Hat JBoss Web Server - Version 5.0 GA": "JWS 5.0",
    "Red Hat JBoss Web Server - Version 5.0.0 GA": "JWS 5.0.0",
    "jws5": "JWS 5.x.x",
    "Red Hat JBoss Web Server - Version 5.1 GA": "JWS 5.1",
    "Red Hat JBoss Web Server - Version 5.1.0 GA": "JWS 5.1.0",
    "Red Hat JBoss Web Server - Version 5.2 GA": "JWS 5.2",
    "Red Hat JBoss Web Server - Version 5.2.0 GA": "JWS 5.2.0",
    "Red Hat JBoss Web Server - Version 5.3 GA": "JWS 5.3",
    "Red Hat JBoss Web Server - Version 5.3.0 GA": "JWS 5.3",
    "Red Hat JBoss Web Server - Version 5.3.1 GA": "JWS 5.3.1",
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
    product_dict = {"name": PRODUCT}
    product_dict[PRESENCE_KEY] = Product.ABSENT

    metadata = {
        "server_id": source["server_id"],
        "source_name": source["source_name"],
        "source_type": source["source_type"],
    }
    subman_consumed = facts.get(SUBMAN_CONSUMED, [])
    installed_with_rpm = facts.get(JWS_INSTALLED_WITH_RPM)
    has_eula_file = facts.get(JWS_HAS_EULA_TXT_FILE)
    jws_has_cert = facts.get(JWS_HAS_CERT)
    tomcat_part_of_redhat = facts.get(TOMCAT_PART_OF_REDHAT_PRODUCT)
    version = get_version(facts.get(JWS_VERSION))
    product_dict[VERSION_KEY] = version
    raw_facts = {}

    # System is subscribed to jws repo, but may or may not have it installed
    if product_entitlement_found(subman_consumed, PRODUCT):
        product_dict[PRESENCE_KEY] = Product.POTENTIAL
        raw_facts[SUBMAN_CONSUMED] = subman_consumed
    # If JWS not installed with rpm, detect potential presence by the presence
    # of a JBossEULA file or tomcat server in JWS_HOME directory
    if tomcat_part_of_redhat:
        product_dict[PRESENCE_KEY] = Product.POTENTIAL
        raw_facts[TOMCAT_PART_OF_REDHAT_PRODUCT] = tomcat_part_of_redhat
    if has_eula_file:
        product_dict[PRESENCE_KEY] = Product.POTENTIAL
        raw_facts[JWS_HAS_EULA_TXT_FILE] = has_eula_file
    # Versions 3.0.0 and over explicitely mention 'JWS' in version string
    if version:
        raw_facts[JWS_VERSION] = facts.get(JWS_VERSION)
        for ver in version:
            if "EWS" not in ver:
                product_dict[PRESENCE_KEY] = Product.PRESENT
                break
            # Versions prior to 3.0.0 can only be detected by the presence of certain
            # EWS components and don't guarantee the installation of EWS
            product_dict[PRESENCE_KEY] = Product.POTENTIAL
            break
    if installed_with_rpm:
        product_dict[PRESENCE_KEY] = Product.PRESENT
        raw_facts[JWS_INSTALLED_WITH_RPM] = installed_with_rpm
    # If jws was installed (not as zip) it will have a certifcate
    # https://mojo.redhat.com/docs/DOC-103535
    # The cert may only be installed when a product is installed with RPM,
    # which we already check for. This step may be unnecessary.
    if jws_has_cert:
        product_dict[PRESENCE_KEY] = Product.PRESENT
        raw_facts[JWS_HAS_CERT] = jws_has_cert

    raw_facts = generate_raw_fact_members(raw_facts)
    metadata[RAW_FACT_KEY] = raw_facts
    product_dict[META_DATA_KEY] = metadata

    return product_dict
