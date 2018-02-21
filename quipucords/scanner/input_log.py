# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Log all input to the filesystem for later debugging."""

import json
import logging
import multiprocessing as mp
import os
import time
import uuid
from django.db import transaction
from api import log_state
from api.source.serializer import SourceSerializer
from api.source import util as view_util
from quipucords import settings

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

UUID_CACHE = None

DEFAULT_MAX_SIZE = 1 << 30  # 1 GiB
DEFAULT_MAX_AGE = 365 * 24 * 60 * 60  # 1 year, except on leap years


@transaction.atomic()
def get_database_uuid():
    """Get the UUID of this database."""
    global UUID_CACHE  # pylint: disable=global-statement
    if UUID_CACHE is not None:
        return UUID_CACHE

    uuid_obj = log_state.DatabaseUUID.objects.all().first()
    if uuid_obj is None:
        uuid_obj = log_state.DatabaseUUID(uuid=uuid.uuid4())
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
    seq = log_state.LatestSequenceNumber.objects.all().first()
    if seq is None:
        seq = log_state.LatestSequenceNumber(number=0)
        seq.save()

    number = seq.number
    seq.number += 1
    seq.save()

    return number


def find_prefix_scan_stat(prefix, dirname):
    """Find files in a directory matching a prefix, and stat them.

    This function exists because os.scandir isn't in Python 3.4, which
    we support.

    :param prefix: the name prefix to search for.
    :param dirname: the directory to scan.

    :returns: a list of (name, stat) pairs for matching files.
    """
    result = []

    for name in os.listdir(dirname):
        if name.startswith(prefix):
            result.append((name, os.stat(os.path.join(dirname, name))))

    return result


# pylint: disable=too-many-instance-attributes
class RotatingLogFile(object):
    """A log file that automatically rotates itself when full."""

    # This class maintains a set of log files with names 'basename-0',
    # 'basename-1', .... It automatically switches to a new one when
    # the last log file is either too big or too old, and removes
    # earlier ones when they exceed the size or age limits. A few
    # flaws:
    #   - It only re-evaluates its log file list on writes. If you
    #     never write anything, it will never rotate the logs.
    #   - It is not safe to use more than one instance of this class
    #     with the same basename. It makes no attempt at locking, and
    #     it doesn't look for notifications of new log files after
    #     it's gathered its initial set.
    #   - It's not thread safe.

    # pylint: disable=too-many-arguments
    def __init__(self, max_size, max_age,
                 step_size=None, step_age=None, dry_run=False):
        """Initialize the RotatingLogFile."""
        # Log files will be named 'basename-0', 'basename-1', etc.
        self.basename = None
        self.dirname = None
        self.max_size = max_size
        self.max_age = max_age
        self.dry_run = dry_run
        self.total_bytes = 0

        # The size and age limits where we start a new log file.
        self.step_size = step_size or (max_size + 9) // 10
        self.step_age = step_age or (max_age + 9) // 10

        # self.log_files will be a list of dicts with entries 'name',
        # 'created', and 'size'. The list will be sorted with the
        # newest entries in the front.
        self.log_files = []
        self.file_counter = 0  # The number of the newest existing log file.

        # The log file we send writes to. This should always be an
        # open File object for the file named by
        # self.log_files[0]['name'], if that exists.
        self.open_log_file = None

        # Whether we've scanned the log directory for old log files.
        self.directory_scanned = False

        self.write_lock = mp.Lock()

    def read_files_from_basename(self, basename):
        """Initialize log_files and file_counter from a basename."""
        self.dirname, self.basename = os.path.split(basename)
        if self.dry_run:
            self.log_files = []
        else:
            self.read_files_from_stats(
                find_prefix_scan_stat(self.basename, self.dirname))

    def read_files_from_stats(self, names_and_stats):
        """Initialize log_files and file_counter from (name, stat) pairs.

        This method is separate to simplify testing.
        """
        for name, stat in names_and_stats:
            if name.startswith(self.basename):
                logger.debug('Found log file %s', name)
                base, _, counter = name.partition('-')
                if base != self.basename:
                    logger.error('Bad log file name: %s', name)
                    continue
                if not counter.isdigit():
                    logger.error('Bad log file name: %s', name)
                    continue

                self.file_counter = max(self.file_counter, int(counter))

                self.log_files.append(
                    {'name': os.path.join(self.dirname, name),
                     'created': stat.st_ctime,
                     'size': stat.st_size})
                self.total_bytes += stat.st_size
        logger.debug('Presorted log file set is %s', self.log_files)

        self.log_files = sorted(self.log_files,
                                key=lambda x: x['created'], reverse=True)
        logger.debug('Initial log file set is %s', self.log_files)

    def remove_oldest_log_file(self):
        """Remove the oldest log file."""
        self.total_bytes -= self.log_files[-1]['size']
        if not self.dry_run:
            os.remove(self.log_files[-1]['name'])
        del self.log_files[-1]

    def new_log_file(self, now=None):
        """Make a new log file."""
        self.file_counter += 1
        new_name = os.path.join(self.dirname,
                                '{0}-{1}'.format(self.basename,
                                                 self.file_counter))
        if self.dry_run:
            size = 0
            created = now
        else:
            self.open_log_file = open(new_name, 'ab')
            stat_result = os.stat(new_name)
            size = stat_result.st_size
            created = stat_result.st_ctime

        # If we were rotating log files a lot, this insert would be a
        # performance issue, but it seems very unlikely that we would
        # rotate that much.
        self.log_files.insert(0, {'name': new_name,
                                  'created': created,
                                  'size': size})

    def rotate_log_files(self, bytes_ahead=0, now=None):
        """Add and remove log files if necessary.

        This function ensures that the log files listed in
        self.log_files are under the max_size and max_age limits and
        that self.open_log_file points to an open log file with enough
        space left before self.step_size to write bytes_ahead bytes.

        :param bytes_ahead: number of bytes to make available in the
            current log file.
        :param now: the current time as number of seconds from epoch,
            or None. Defaults to time.time().
        """
        now = now or time.time()

        # Remove old log files
        while (self.log_files and
               now - self.log_files[-1]['created'] > self.max_age):
            self.remove_oldest_log_file()

        while (self.log_files and
               self.total_bytes + bytes_ahead > self.max_size):
            self.remove_oldest_log_file()

        # Maybe create new log file
        if not self.log_files or \
           self.log_files[0]['size'] + bytes_ahead > self.step_size or \
           now - self.log_files[0]['created'] > self.step_age:
            self.new_log_file(now)

        # Maybe open the log file
        if not self.open_log_file and not self.dry_run:
            self.open_log_file = open(self.log_files[0]['name'], 'ab')

    def write_record(self, record, now=None):
        """Write to the rotating log."""
        binary_record = (json.dumps(record) + '\n').encode(encoding='utf-8')
        self.rotate_log_files(bytes_ahead=len(binary_record), now=now)

        # A single record is always written to exactly one log file,
        # even if the record is larger than self.step_size. (If this
        # happens with any frequency, then self.step_size is way too
        # small.)
        if not self.dry_run:
            with self.write_lock:
                self.open_log_file.write(binary_record)
                self.open_log_file.flush()
        self.log_files[0]['size'] += len(binary_record)
        self.total_bytes += len(binary_record)


INPUT_LOG = None


def log_record(record):
    """Write a new record to the input log.

    :param record: the record. a Python dict, with JSON-compatible values.
    """
    global INPUT_LOG  # pylint: disable=global-statement
    if INPUT_LOG is None:
        INPUT_LOG = RotatingLogFile(max_size=DEFAULT_MAX_SIZE,
                                    max_age=DEFAULT_MAX_AGE)
        INPUT_LOG.read_files_from_basename(settings.INPUT_LOG_BASENAME)

    record['database_uuid'] = str(get_database_uuid())
    record['sequence_number'] = next_sequence_number()

    INPUT_LOG.write_record(record)


# pylint: disable=too-many-arguments
def log_fact(host, fact, value, scan_job, scan_task, source):
    """Write a new fact to the input log.

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
    """Disable the input log for testing purposes."""
    global INPUT_LOG  # pylint: disable=global-statement
    INPUT_LOG = RotatingLogFile(max_size=DEFAULT_MAX_SIZE,
                                max_age=DEFAULT_MAX_AGE,
                                dry_run=True)
    INPUT_LOG.read_files_from_basename(settings.INPUT_LOG_BASENAME)


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
