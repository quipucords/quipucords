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

from api import messages
from api.models import (ScanTask,
                        ServerInformation,
                        Source)
from api.serializers import FactCollectionSerializer

from django.utils.translation import ugettext as _


ERRORS_KEY = 'errors'
INVALID_SOURCES_KEY = 'invalid_sources'
VALID_SOURCES_KEY = 'valid_sources'

# JSON attribute constants
SOURCES_KEY = 'sources'
SOURCE_KEY = 'source'
SERVER_ID_KEY = 'server_id'
SOURCE_TYPE_KEY = 'source_type'
SOURCE_NAME_KEY = 'source_name'
FACTS_KEY = 'facts'

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def build_sources_from_tasks(tasks):
    """Build sources for a set of tasks.

    :param tasks: ScanTask objects used to build results
    :returns: dict containing sources structure for facts endpoint
    """
    server_id = ServerInformation.create_or_retreive_server_id()
    sources = []
    for inspect_task in tasks:
        if inspect_task.scan_type != ScanTask.SCAN_TYPE_INSPECT:
            continue
        task_facts = inspect_task.get_facts()
        if task_facts:
            source = inspect_task.source
            if source is not None:
                source_dict = {
                    SERVER_ID_KEY: server_id,
                    SOURCE_NAME_KEY: source.name,
                    SOURCE_TYPE_KEY: source.source_type,
                    FACTS_KEY: task_facts}
                sources.append(source_dict)
    return sources


def validate_fact_collection_json(fact_collection_json):
    """Validate details_report field.

    :param fact_collection_json: dict representing a details report
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
    server_id = source_json.get(SERVER_ID_KEY)
    has_error = False
    if not server_id:
        has_error = True
        invalid_field_obj[SERVER_ID_KEY] = _(
            messages.FC_REQUIRED_ATTRIBUTE)

    source_type = source_json.get(SOURCE_TYPE_KEY)
    source_name = source_json.get(SOURCE_NAME_KEY)

    if not source_name:
        has_error = True
        invalid_field_obj[SOURCE_NAME_KEY] = _(
            messages.FC_REQUIRED_ATTRIBUTE)

    if not source_type:
        has_error = True
        invalid_field_obj[SOURCE_TYPE_KEY] = _(
            messages.FC_REQUIRED_ATTRIBUTE)

    if not has_error and not isinstance(source_name, str):
        has_error = True
        invalid_field_obj[SOURCE_NAME_KEY] = _(
            messages.FC_SOURCE_NAME_NOT_STR)

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


def create_fact_collection(json_fact_collection):
    """Create details report.

    Fact collection consists of a DetailsReport record
    :param json_fact_collection: dict representing a details report
    :returns: The newly created DetailsReport
    """
    # Create new details report
    serializer = FactCollectionSerializer(data=json_fact_collection)
    if serializer.is_valid():
        details_report = serializer.save()
        logger.debug('Fact collection created: %s', details_report)
        return details_report

    logger.error('Fact collection could not be persisted.')
    logger.error('Invalid json_fact_collection: %s',
                 json_fact_collection)
    logger.error('DetailsReport errors: %s', serializer.errors)

    return None
