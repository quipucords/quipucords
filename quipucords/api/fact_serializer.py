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

"""Serializer for system facts models"""

from rest_framework.serializers import ModelSerializer, ValidationError
from api.fact_model import Fact, FactCollection
from django.utils.translation import ugettext as _


class FactSerializer(ModelSerializer):
    """Serializer for the Fact model."""
    class Meta:
        """Meta class for FactSerializer."""
        model = Fact
        fields = ('etc_release_name', 'etc_release_release',
                  'etc_release_version', 'connection_uuid')


class FactCollectionSerializer(ModelSerializer):
    """Serializer for the FactCollection model"""
    facts = FactSerializer(many=True)

    class Meta:
        """Meta class for FactCollectionSerializer."""
        model = FactCollection
        fields = '__all__'

    def create(self, validated_data):
        facts_data = validated_data.pop('facts')
        report = FactCollection.objects.create(**validated_data)
        for fact_data in facts_data:
            new_fact = Fact.objects.create(**fact_data)
            report.facts.add(new_fact)
        report.save()
        return report

    @staticmethod
    def validate_facts(facts):
        """Make sure the facts list is present."""
        if not facts:
            raise ValidationError(_('A least one fact is required.'))
        return facts
