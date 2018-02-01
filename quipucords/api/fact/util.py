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

"""Util for validating and persisting source facts."""

import logging
from django.db import transaction
from django.utils.translation import ugettext as _
import api.messages as messages
from api.models import Source, FactCollection
from api.serializers import FactCollectionSerializer


ERRORS_KEY = 'errors'
INVALID_SOURCES_KEY = 'invalid_sources'
VALID_SOURCES_KEY = 'valid_sources'

# JSON attribute constants
SOURCES_KEY = 'sources'
SOURCE_KEY = 'source'
SOURCE_ID_KEY = 'source_id'
SOURCE_TYPE_KEY = 'source_type'
FACTS_KEY = 'facts'

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def validate_fact_collection_json(fact_collection_json):
    """Validate fact_collection field.

    :param fact_collection_json: dict representing a fact collection
    :returns: bool indicating if there are errors and dict with result.
    """
    if not fact_collection_json.get(SOURCES_KEY):
        return True, {SOURCES_KEY: _(messages.FC_REQUIRED_ATTRIBUTE)}

    return _validate_sources_json(fact_collection_json.get(SOURCES_KEY))


def _validate_sources_json(sources_json):
    """Validate sources field.

    :param sources_json: list of sources.  Each source is a dict.
    :returns: bool indicating if there are errors and
    dict with 2 lists.  Valid and invalid sources.
    """
    valid_sources = []
    invalid_sources = []
    has_errors = False
    for source_json in sources_json:
        source_error, result = _validate_source_json(source_json)
        if source_error:
            has_errors = True
            invalid_sources.append(result)
        else:
            valid_sources.append(source_json)

    return has_errors, {
        VALID_SOURCES_KEY: valid_sources,
        INVALID_SOURCES_KEY: invalid_sources}


def _validate_source_json(source_json):
    """Validate source fields.

    :param source_json: The dict representing facts for a source
    :returns: bool indicating if there are errors and
    dict with error result or None.
    """
    invalid_field_obj = {}
    source_id = source_json.get(SOURCE_ID_KEY)
    has_error = False
    if not source_id:
        has_error = True
        invalid_field_obj[SOURCE_ID_KEY] = _(
            messages.FC_REQUIRED_ATTRIBUTE)

    if not has_error and not isinstance(source_id, int):
        has_error = True
        invalid_field_obj[SOURCE_ID_KEY] = _(
            messages.FC_SOURCE_ID_NOT_INT)

    if not has_error:
        source = Source.objects.filter(pk=source_id).first()
        if not source:
            has_error = True
            invalid_field_obj[SOURCE_ID_KEY] = _(
                messages.FC_SOURCE_NOT_FOUND % source_id)

    source_type = source_json.get(SOURCE_TYPE_KEY)
    if not source_type:
        has_error = True
        invalid_field_obj[SOURCE_TYPE_KEY] = _(
            messages.FC_REQUIRED_ATTRIBUTE)

    if not has_error and not \
            [valid_type for valid_type in Source.SOURCE_TYPE_CHOICES
             if valid_type[0] == source_type]:
        has_error = True
        valid_choices = ', '.join(
            [valid_type[0] for valid_type in Source.SOURCE_TYPE_CHOICES])
        invalid_field_obj[SOURCE_TYPE_KEY] = _(
            messages.FC_MUST_BE_ONE_OF % valid_choices)

    facts = source_json.get(FACTS_KEY)
    if not facts:
        has_error = True
        invalid_field_obj[FACTS_KEY] = _(
            messages.FC_REQUIRED_ATTRIBUTE)

    if has_error:
        error_json = {}
        error_json[SOURCE_KEY] = source_json
        error_json[ERRORS_KEY] = invalid_field_obj
        return True, error_json
    return False, None


@transaction.atomic
def get_or_create_fact_collection(json_fact_collection, scan_job=None):
    """Create fact collection.

    Fact collection consists of a FactCollection record and a
    corresponding JSON file with the name <fact_collection_id>.json
    :param json_fact_collection: dict representing a fact collection
    :param scan_job: scanjob to be associated with this fact_collection
    :returns: The newly created FactCollection
    """
    fact_collection = None
    if scan_job is not None:
        # check for existing fact collection
        fact_collection_id = scan_job.fact_collection_id
        fact_collection = FactCollection.objects.filter(
            id=fact_collection_id).first()

    if fact_collection is None:
        # Create new fact collection
        serializer = FactCollectionSerializer(data=json_fact_collection)
        if serializer.is_valid():
            fact_collection = serializer.save()
            logger.debug('Fact collection created: %s', fact_collection)
        else:
            logger.error('Fact collection could not be persisted.')
            logger.error('Invalid json_fact_collection: %s',
                         json_fact_collection)
            logger.error('FactCollection errors: %s', serializer.errors)

        # Update scan job if there is one
        if scan_job is not None:
            scan_job.fact_collection_id = fact_collection.id
            scan_job.save()
            fact_collection.save()
            logger.debug('Fact collection %d associated with scanjob %d',
                         fact_collection.id,
                         scan_job.id)

    return fact_collection
