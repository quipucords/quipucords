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


class Engine():
    """Engine that produces fingerprints from
    facts"""
    # pylint: disable= no-self-use

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
        fingerprint = {'fact_collection_id': fact_collection_id,
                       'os_name': fact['etc_release_name'],
                       'os_release': fact['etc_release_release'],
                       'os_version': fact['etc_release_version']}

        return fingerprint
