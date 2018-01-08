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

import os
import json
import copy
from django.conf import settings
from django.utils.translation import ugettext as _
import api.messages as messages
from api.models import Source, FactCollection


ERRORS_KEY = 'errors'
RESULT_KEY = 'result'
INVALID_SOURCES_KEY = 'invalid_sources'
VALID_SOURCES_KEY = 'valid_sources'

# JSON attribute constants
SOURCES_KEY = 'sources'
SOURCE_KEY = 'source'
SOURCE_ID_KEY = 'source_id'
SOURCE_TYPE_KEY = 'source_type'
FACTS_KEY = 'facts'


def validate_fact_collection_json(fact_collection_json):
    """Validate fact_collection field.

    :param fact_collection_json: dict representing a fact collection
    :returns: dict with bool indicating error and result.
    """
    if not fact_collection_json.get(SOURCES_KEY):
        return {ERRORS_KEY: True,
                RESULT_KEY: {
                    SOURCES_KEY: _(messages.FC_REQUIRED_ATTRIBUTE)}}

    return _validate_sources_json(fact_collection_json.get(SOURCES_KEY))


def _validate_sources_json(sources_json):
    """Validate sources field.

    :param sources_json: list of sources.  Each source is a dict.
    :returns: dict with 2 lists.  Valid and invalid sources.
    """
    valid_sources = []
    invalid_sources = []
    for source_json in sources_json:
        result = _validate_source_json(source_json)
        if result[ERRORS_KEY]:
            invalid_sources.append(result[RESULT_KEY])
        else:
            valid_sources.append(source_json)

    has_errors = len(invalid_sources) > 0
    return {ERRORS_KEY: has_errors,
            RESULT_KEY: {
                VALID_SOURCES_KEY: valid_sources,
                INVALID_SOURCES_KEY: invalid_sources}}


def _validate_source_json(source_json):
    """Validate source fields.

    :param source_json: The dict representing facts for a source
    :returns: None if no errors or a JSON dict with the errors
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

    result = {ERRORS_KEY: has_error}
    if has_error:
        error_json = {}
        error_json[SOURCE_KEY] = source_json
        error_json[ERRORS_KEY] = invalid_field_obj
        result[RESULT_KEY] = error_json
    return result


def create_fact_collection(fact_collection_json):
    """Create fact collection.

    Fact collection consists of a FactCollection record and a
    corresponding JSON file with the name <fact_collection_id>.json
    :param fact_collection_json: dict representing a fact collection
    :returns: The newly created FactCollection
    """
    # Create fact collection
    fact_collection = FactCollection()
    fact_collection.save()

    # Save raw facts and update fact collection
    fact_collection.path = write_raw_facts(
        fact_collection.id, fact_collection_json)
    fact_collection.save()

    return fact_collection


def read_raw_facts(fc_id):
    """Read raw facts from json file.

    :param fc_id: Fact collection id to read
    "returns: JSON data as dict or None if invalid fc_id
    """
    if os.path.exists(settings.FACTS_DIR):
        with open(_build_path(fc_id), 'r') as raw_fact_file:
            data = json.load(raw_fact_file)
            return data

    return None


def write_raw_facts(fc_id, data):
    """Write raw facts to json file.

    :param fc_id: Fact collection id to write
    :param data: JSON data as dict to write
    "returns: Fully qualified path to json file
    """
    if not os.path.exists(settings.FACTS_DIR):
        os.makedirs(settings.FACTS_DIR)

    file_path = _build_path(fc_id)
    data_copy = copy.deepcopy(data)
    data_copy['fact_collection_id'] = fc_id
    with open(file_path, 'w') as raw_fact_file:
        json.dump(data_copy, raw_fact_file)

    return file_path


def _build_path(fc_id):
    """Build path to json file."""
    return '%s/%d.json' % (settings.FACTS_DIR, fc_id)
