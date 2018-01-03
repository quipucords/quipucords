#
# Copyright (c) 2017 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#

"""Fingerprint engine ingests raw facts and produces system finger prints."""

from datetime import datetime


class Engine():
    """Engine that produces fingerprints from facts."""


    def process_sources(self, fact_collection_id, sources):
        pass

    def process_source(self, fact_collection_id, source):
        pass

    # pylint: disable= no-self-use
    def process_facts(self, fact_collection_id, facts):
        """Process facts and convert to fingerprints.

        :param fact_collection_id: id of fact collection
        associated with facts
        :param facts: facts to process
        :returns: fingerprints produced from facts
        """
        fingerprints = []
        for fact in facts:
            fingerprints.append(self.process_fact(fact_collection_id, fact))
        return fingerprints

    def process_fact(self, fact_collection_id, fact):
        """Process a fact and convert to a fingerprint.

        :param fact_collection_id: id of fact collection
        associated with facts
        :param facts: fact to process
        :returns: fingerprint produced from fact
        """
        # Set fact collection id
        fingerprint = {'fact_collection_id': fact_collection_id}

        # Set OS information
        if fact.get('etc_release_name'):
            fingerprint['os_name'] = fact['etc_release_name']

        if fact.get('etc_release_version'):
            fingerprint['os_version'] = fact['etc_release_version']

        if fact.get('etc_release_release'):
            fingerprint['os_release'] = fact['etc_release_release']

        # Set connection information
        if fact.get('connection_uuid'):
            fingerprint['connection_uuid'] = fact['connection_uuid']

        if fact.get('connection_host'):
            fingerprint['connection_host'] = fact['connection_host']

        if fact.get('connection_port'):
            fingerprint['connection_port'] = fact['connection_port']

        # Set CPU facts
        if fact.get('cpu_count'):
            fingerprint['cpu_count'] = fact['cpu_count']

        if fact.get('cpu_core_per_socket'):
            fingerprint['cpu_core_per_socket'] = fact['cpu_core_per_socket']

        if fact.get('cpu_siblings'):
            fingerprint['cpu_siblings'] = fact['cpu_siblings']

        if fact.get('cpu_hyperthreading') is not None:
            fingerprint['cpu_hyperthreading'] = fact['cpu_hyperthreading']

        if fact.get('cpu_socket_count'):
            fingerprint['cpu_socket_count'] = fact['cpu_socket_count']

        if fact.get('cpu_core_count'):
            fingerprint['cpu_core_count'] = fact['cpu_core_count']

        # Determine system_creation_date
        system_creation_date = None
        if fact.get('date_anaconda_log'):
            system_creation_date = datetime.strptime(
                fact['date_anaconda_log'], '%Y-%m-%d')

        if system_creation_date and fact.get('date_yum_history'):
            date_yum_history = datetime.strptime(
                fact['date_yum_history'], '%Y-%m-%d')
            if date_yum_history < system_creation_date:
                system_creation_date = date_yum_history

        if system_creation_date:
            fingerprint['system_creation_date'] = system_creation_date.date()

        # Determine if running on VM or bare metal
        if fact.get('virt_what_type') or fact.get('virt_type'):
            if fact.get('virt_what_type') == 'bare metal':
                fingerprint['infrastructure_type'] = 'bare_metal'
            elif fact.get('virt_type'):
                fingerprint['infrastructure_type'] = 'virtualized'
            else:
                # virt_what_type is not bare metal or None
                # (since both cannot be)
                fingerprint['infrastructure_type'] = 'unknown'
        else:
            fingerprint['infrastructure_type'] = 'unknown'

        # Determine if VM facts
        fingerprint['virtualized_is_guest'] = bool(
            fact.get('virt_virt') == 'virt-guest')

        if fact.get('virt_type'):
            fingerprint['virtualized_type'] = fact['virt_type']

        if fact.get('virt_num_guests'):
            fingerprint['virtualized_num_guests'] = fact['virt_num_guests']

        if fact.get('virt_num_running_guests'):
            fingerprint['virtualized_num_running_guests'] =\
                fact['virt_num_running_guests']

        return fingerprint
