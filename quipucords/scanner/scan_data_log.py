# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Log all scan data to the filesystem for later debugging."""

import json
import logging
from logging import handlers
import multiprocessing as mp
import uuid
from django.db import transaction
from api import scan_data_log_state
from api.source.serializer import SourceSerializer
from api.source import util as view_util
from quipucords import settings

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

UUID_CACHE = None

NUM_LOG_FILES = 10  # Divide the log into 10 different files


@transaction.atomic()
def get_database_uuid():
    """Get the UUID of this database."""
    global UUID_CACHE  # pylint: disable=global-statement
    if UUID_CACHE is not None:
        return UUID_CACHE

    uuid_obj = scan_data_log_state.DatabaseUUID.objects.all().first()
    if uuid_obj is None:
        uuid_obj = scan_data_log_state.DatabaseUUID(uuid=uuid.uuid4())
        uuid_obj.save()
    UUID_CACHE = uuid_obj.uuid

    return uuid_obj.uuid


# This is a potential performance bottleneck since we are touching the
# database every time we write a record. This isn't necessary - we
# could get the state of the counter by reading the last few entries
# of the existing log files on startup. I don't plan to implement that
# unless we find that this is actually a problem.
@transaction.atomic()
def next_sequence_number():
    """Get the next sequence number and increment the counter."""
    seq = scan_data_log_state.LatestSequenceNumber.objects.all().first()
    if seq is None:
        seq = scan_data_log_state.LatestSequenceNumber(number=0)
        seq.save()

    number = seq.number
    seq.number += 1
    seq.save()

    return number


# We use the standard Python loggers when possible, but with two main
# differences:

# 1. We have a custom log formatter. The standard Python log format is
#    nice for humans to read, but not nice for machines to parse. So
#    we have JSONFormatter, which writes log records as plain JSON
#    dicts that are easy to parse.

# 2. We don't use LogRecord objects. Almost none of their attributes
#    apply to what we're doing, and there doesn't seem to be any
#    advantage to using them, so we just pass plain dictionaries
#    around.

class JSONFormatter(logging.Formatter):
    """Write scan data log messages as plain JSON dicts."""

    def format(self, record):
        """Format a JSON dict as a JSON string."""
        # StreamHandler will add a '\n' after every record.
        return json.dumps(record)


# We use multiprocessing and not threads, so we need to use a
# multiprocessing lock.
class MultiprocessRotatingFileHandler(handlers.RotatingFileHandler):
    """A RotatingFileHandler that uses a multiprocessing lock."""

    def createLock(self):
        """Create a lock."""
        self.lock = mp.RLock()


_HANDLER = MultiprocessRotatingFileHandler(
    filename=settings.SCAN_DATA_LOG,
    encoding='utf-8',
    maxBytes=settings.SCAN_DATA_LOG_MAX_BYTES // NUM_LOG_FILES,
    backupCount=NUM_LOG_FILES)
_HANDLER.setFormatter(JSONFormatter())

_DRY_RUN = False


def log_record(record):
    """Write a new record to the scan data log.

    :param record: the record. a Python dict, with JSON-compatible values.
    """
    record['database_uuid'] = str(get_database_uuid())
    record['sequence_number'] = next_sequence_number()

    if record['sequence_number'] % 100 == 0:
        logger.info('Logging scan data to %s, dry_run=%s',
                    settings.SCAN_DATA_LOG, _DRY_RUN)

    if not _DRY_RUN:
        _HANDLER.emit(record)


# pylint: disable=too-many-arguments
def log_fact(host, fact, value, scan_job, scan_task, source):
    """Write a new fact to the scan data log.

    :param host: string. the name of the host the fact came from.
    :param fact: json object. The fact identifier.
    :param value: the value of the fact.
    :param scan_job: the scan job, as an int.
    :param scan_task: the scan task, as an int.
    :param source: the source, as a JSON dict.
    """
    log_record({'host': host,
                'fact': fact,
                'value': value,
                'scan_job': scan_job,
                'scan_task': scan_task,
                'source': source})


def disable_log_for_test():
    """Disable the scan data log for testing purposes."""
    global _DRY_RUN  # pylint: disable=global-statement
    _DRY_RUN = True


RAW_PARAMS = '_raw_params'


def log_ansible_result(result, scan_task):
    """Log the results of a shell command.

    :param result: the Ansible result object, as a Python dict.
    :param scan_task: the ScanTask of this Ansible task.
    """
    # pylint: disable=protected-access
    args = result._task.args

    source_json = SourceSerializer(scan_task.source).data
    view_util.expand_credential(source_json)
    scan_jobs = list(scan_task.scanjob_set.all())

    # len(scan_jobs) should be 1
    if len(scan_jobs) > 1:
        logger.warning('ScanTask %s associated to multiple ScanJobs %s',
                       scan_task.id, [job.id for job in scan_jobs])

    if RAW_PARAMS in args:
        log_fact(result._host.name,
                 {'type': 'shell', 'command': args[RAW_PARAMS]},
                 result._result,
                 scan_jobs[0].id,
                 scan_task.id,
                 source_json)
    # If _raw_params isn't in args, then args is not a raw command and
    # we don't need to record it. This occurs for set_facts tasks.


def safe_log_ansible_result(result, scan_task):
    """Log the results of a shell command.

    This function should always return.

    :param result: the Ansible result object, as a Python dict.
    :param scan_task: the ScanTask of this Ansible task.
    """
    try:
        log_ansible_result(result, scan_task)
    except Exception:  # pylint: disable=broad-except
        pass
