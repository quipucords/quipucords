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

"""Fingerprint engine ingests raw facts and produces system finger prints"""

from datetime import datetime


class Engine():
    """Engine that produces fingerprints from
    facts"""
    # pylint: disable= no-self-use,too-many-branches,too-many-statements

    def process_facts(self, fact_collection_id, facts):
        """Process facts and convert to fingerprints

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
        """Process a fact and convert to a fingerprint

        :param fact_collection_id: id of fact collection
        associated with facts
        :param facts: fact to process
        :returns: fingerprint produced from fact
        """
        # Set fact collection id
        fingerprint = {'fact_collection_id': fact_collection_id}

        # Set OS information
        if 'etc_release_name' in fact and fact['etc_release_name']:
            fingerprint['os_name'] = fact['etc_release_name']

        if 'etc_release_version' in fact and fact['etc_release_version']:
            fingerprint['os_version'] = fact['etc_release_version']

        if 'etc_release_release' in fact and fact['etc_release_release']:
            fingerprint['os_release'] = fact['etc_release_release']

        # Set connection information
        if 'connection_uuid' in fact and fact['connection_uuid']:
            fingerprint['connection_uuid'] = fact['connection_uuid']

        if 'connection_host' in fact and fact['connection_host']:
            fingerprint['connection_host'] = fact['connection_host']

        if 'connection_port' in fact and fact['connection_port']:
            fingerprint['connection_port'] = fact['connection_port']

        # Set CPU facts
        if 'cpu_count' in fact and fact['cpu_count']:
            fingerprint['cpu_count'] = fact['cpu_count']

        if 'cpu_core_per_socket' in fact and fact['cpu_core_per_socket']:
            fingerprint['cpu_core_per_socket'] = fact['cpu_core_per_socket']

        if 'cpu_siblings' in fact and fact['cpu_siblings']:
            fingerprint['cpu_siblings'] = fact['cpu_siblings']

        if 'cpu_hyperthreading' in fact\
                and fact['cpu_hyperthreading'] is not None:
            fingerprint['cpu_hyperthreading'] = fact['cpu_hyperthreading']

        if 'cpu_socket_count' in fact and fact['cpu_socket_count']:
            fingerprint['cpu_socket_count'] = fact['cpu_socket_count']

        if 'cpu_core_count' in fact and fact['cpu_core_count']:
            fingerprint['cpu_core_count'] = fact['cpu_core_count']

        # Determine system_creation_date
        system_creation_date = None
        if 'date_anaconda_log' in fact and fact['date_anaconda_log']:
            system_creation_date = datetime.strptime(
                fact['date_anaconda_log'], '%Y-%m-%d')

        if system_creation_date\
                and 'date_yum_history' in fact\
                and fact['date_yum_history']:
            date_yum_history = datetime.strptime(
                fact['date_yum_history'], '%Y-%m-%d')
            if date_yum_history < system_creation_date:
                system_creation_date = date_yum_history

        if system_creation_date:
            fingerprint['system_creation_date'] = system_creation_date.date()

        # Determine if running on VM or bare metal
        if ('virt_what_type' in fact and fact['virt_what_type'])\
                or ('virt_type' in fact and fact['virt_type']):
            if fact['virt_what_type'] == 'bare metal':
                fingerprint['infrastructure_type'] = 'bare_metal'
            elif 'virt_type' in fact and fact['virt_type']:
                fingerprint['infrastructure_type'] = 'virtualized'
            else:
                # virt_what_type is not bare metal or None
                # (since both cannot be)
                fingerprint['infrastructure_type'] = 'unknown'
        else:
            fingerprint['infrastructure_type'] = 'unknown'

        # Determine if VM facts
        fingerprint['virtualized_is_guest'] = bool(
            fact['virt_virt'] == 'virt-guest')

        if 'virt_type' in fact and fact['virt_type']:
            fingerprint['virtualized_type'] = fact['virt_type']

        if 'virt_num_guests' in fact and fact['virt_num_guests']:
            fingerprint['virtualized_num_guests'] = fact['virt_num_guests']

        if 'virt_num_running_guests' in fact\
                and fact['virt_num_running_guests']:
            fingerprint['virtualized_num_running_guests'] =\
                fact['virt_num_running_guests']

        return fingerprint
