# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Log all input to the filesystem for later debugging."""

import io
import json
import logging
import multiprocessing as mp
import os
import uuid
from django.db import transaction
from api import log_state
from quipucords import settings

logger = logging.logger(__name__)

UUID_CACHE = None


@transaction.atomic()
def get_sonar_uuid():
    """Get the UUID of this Sonar installation."""
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

    def __init__(self, basename, max_size, max_age,
                 step_size=None, step_age=None):
        # Log files will be named 'basename-0', 'basename-1', etc.
        self.basename = basename
        self.max_size = max_size
        self.max_age = max_age

        # The size and age limits where we start a new log file.
        self.step_size = step_size or max_size // 10
        self.step_age = step_age or max_age // 10

        # self.log_files will be a list of dicts with entries 'name',
        # 'created', and 'size'. The list will be sorted with the
        # newest entries in the front.
        self.log_files = []
        self.file_counter = 0

        for name in os.listdir(settings.INPUT_LOG_DIRECTORY):
            if name.startswith(basename):
                base, sep, counter = name.partition('-')
                if base != basename:
                    logger.error('Bad log file name: %s', name)
                    continue

                self.file_counter = max(self.file_counter, int(counter))

                stat_result = os.stat(name)
                self.log_files.append({'name': name,
                                       'created': stat_result.st_mtime,
                                       'size': stat_result.st_size})

        self.log_files = sorted(self.log_files,
                                key=lambda x: x['created'], reverse=True)
        self.fp = open(log_files[0]['name'], 'ab')

    def ensure_log_file_ready(self):
        if not self.log_files:
            name = '{0}-{1}'.format(self.basename, self.file_counter)
            # We handle the encoding ourselves and write to fp in
            # binary mode so that a) we can guarantee consistent
            # encoding of the log files and b) we can count the number
            # of bytes we're writing.
            self.fp = open(name, 'ab')
            stat_resul


INPUT_LOG = None
WRITE_LOCK = mp.Lock()


def log_fact(host, fact, value):
    """Write a new fact to the input log.

    :param host: string. the name of the host the fact came from.
    :param fact: json object. The fact identifier.
    :param value: the value of the fact.
    """
    global INPUT_LOG  # pylint: disable=global-statement
    if INPUT_LOG is None:
        INPUT_LOG = open(settings.INPUT_LOG_FILE, 'a')

    database_uuid = get_sonar_uuid()
    seq = next_sequence_number()

    with WRITE_LOCK:
        INPUT_LOG.write(json.dumps({'database_uuid': str(database_uuid),
                                    'host': host,
                                    'fact': fact,
                                    'sequence_number': seq,
                                    'result': value}))
        INPUT_LOG.write('\n')
        INPUT_LOG.flush()


def disable_log_for_test():
    """Disable the input log for testing purposes."""
    global INPUT_LOG  # pylint: disable=global-statement
    INPUT_LOG = io.StringIO()


RAW_PARAMS = '_raw_params'


def log_ansible_result(result):
    """Log a shell command."""
    # pylint: disable=protected-access
    args = result._task.args

    if RAW_PARAMS in args:
        log_fact(result._host.name,
                 {'type': 'shell', 'command': args[RAW_PARAMS]},
                 result._result)
    # If _raw_params isn't in args, then args is not a raw command and
    # we don't need to record it. This occurs for set_facts tasks.
