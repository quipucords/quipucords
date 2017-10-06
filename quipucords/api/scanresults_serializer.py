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
"""Module for serializing all model object for database storage"""

from rest_framework.serializers import ModelSerializer
from api.scanresults_model import ScanJobResults, Results, ResultKeyValue


class ResultKeyValueSerializer(ModelSerializer):
    """Serializer for the ResultKeyValue model"""

    class Meta:
        model = ResultKeyValue
        fields = '__all__'


class ResultsSerializer(ModelSerializer):
    """Serializer for the Results model"""

    class Meta:
        model = Results
        fields = '__all__'


class ScanJobResultsSerializer(ModelSerializer):
    """Serializer for the ScanJobResults model"""

    class Meta:
        model = ScanJobResults
        fields = '__all__'
