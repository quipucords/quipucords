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
import multiprocessing as mp
import uuid
from django.db import transaction
from api import log_state
from quipucords import settings

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
    global INPUT_LOG
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
    else:
        print('*** Ansible result:', result)
    # If _raw_params isn't in args, then args is not a raw command and
    # we don't need to record it. This occurs for set_facts tasks.
