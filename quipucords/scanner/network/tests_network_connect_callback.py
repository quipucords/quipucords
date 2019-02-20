#
# Copyright (c) 2019 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test the connect callback capabilities."""

# pylint: disable=ungrouped-imports
from api.models import (Credential,
                        ScanTask,
                        Source)

from django.test import TestCase

from scanner.network.connect import ConnectResultStore
from scanner.network.connect_callback import ConnectResultCallback
from scanner.test_util import create_scan_job


def build_event(host, return_code=0,
                stderr=False, msg=False, event=False):
    """Build event dictionary matching ansible runner response."""
    event_dict = dict()
    event_data = dict()
    res_dict = dict()
    event_dict['event'] = event
    event_data['host'] = host
    res_dict['rc'] = return_code
    if stderr:
        res_dict['stderr'] = stderr
    if msg:
        res_dict['msg'] = msg
    event_data['res'] = res_dict
    event_dict['event_data'] = event_data
    return event_dict


# pylint: disable=too-many-instance-attributes
class TestConnectResultCallback(TestCase):
    """Test ConnectResultCallback."""

    def setUp(self):
        """Set up required for tests."""
        self.cred = Credential(
            name='cred1',
            username='username',
            password='password',
            ssh_keyfile='keyfile',
            become_method='sudo',
            become_user='root',
            become_password='become')
        self.cred.save()

        self.source = Source(
            name='source1',
            hosts='["1.2.3.4", "1.2.3.5", "1.2.3.6"]',
            source_type='network',
            port=22)
        self.source.save()
        self.source.credentials.add(self.cred)
        self.source.save()

        self.scan_job, self.scan_task = create_scan_job(
            self.source, ScanTask.SCAN_TYPE_CONNECT)

    def test_task_on_ok(self):
        """Test the callback on ok."""
        results_store = ConnectResultStore(self.scan_task)
        callback = ConnectResultCallback(results_store, self.cred, self.source)
        events = []
        events.append(build_event(host='1.2.3.4',
                                  event='runner_on_ok'))
        events.append(build_event(host='1.2.3.5', return_code=1,
                                  event='runner_on_ok'))
        events.append(build_event(host='1.2.3.6',
                                  return_code=None, event='runner_on_ok'))
        for event in events:
            callback.runner_event(event)
        self.assertEqual(callback.result_store.scan_task.systems_count, 3)
        self.assertEqual(callback.result_store.scan_task.systems_scanned, 1)
        self.assertEqual(callback.result_store.scan_task.systems_failed, 0)

    def test_task_on_failed(self):
        """Test the callback on failed."""
        results_store = ConnectResultStore(self.scan_task)
        callback = ConnectResultCallback(results_store,
                                         self.cred,
                                         self.source)
        events = []
        events.append(build_event(host='1.2.3.4',
                                  event='runner_on_failed'))
        events.append(build_event(host='1.2.3.5',
                                  event='runner_on_failed',
                                  stderr='permission denied'))
        for event in events:
            callback.runner_event(event)
        self.assertEqual(callback.result_store.scan_task.systems_failed, 0)
        self.assertEqual(callback.result_store.scan_task.systems_count, 3)

    def test_task_on_unreachable(self):
        """Test the callback on unreachable."""
        results_store = ConnectResultStore(self.scan_task)
        callback = ConnectResultCallback(results_store,
                                         self.cred,
                                         self.source)
        events = []
        events.append(build_event(host='1.2.3.4',
                                  event='runner_on_unreachable'))
        events.append(build_event(host='1.2.3.5',
                                  event='runner_on_unreachable',
                                  msg='permission denied'))
        for event in events:
            callback.runner_event(event)
        self.assertEqual(callback.result_store.scan_task.systems_failed, 0)
        self.assertEqual(callback.result_store.scan_task.systems_unreachable,
                         1)
        self.assertEqual(callback.result_store.scan_task.systems_count, 3)

    def test_exceptions_for_tasks(self):
        """Test exception for each task."""
        results_store = None
        callback = ConnectResultCallback(results_store, self.cred, self.source)
        events = []
        events.append(build_event(host='1.2.3.4',
                                  event='runner_on_ok'))
        events.append(build_event(host='1.2.3.4',
                                  event='runner_on_failed'))
        events.append(build_event(host='1.2.3.4',
                                  event='runner_on_unreachable'))
        for event in events:
            with self.assertRaises(Exception):
                callback.runner_event(event)

    def test_unknown_event_response(self):
        """Test unknown event response."""
        results_store = ConnectResultStore(self.scan_task)
        callback = ConnectResultCallback(results_store,
                                         self.cred,
                                         self.source)
        events = []
        events.append(build_event(host='1.2.3.4',
                                  event='runner_on_unknown_event'))
        for event in events:
            callback.runner_event(event)
