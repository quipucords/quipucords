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
"""Test the API application."""

from unittest.mock import patch
import json
from django.test import TestCase
from django.core.urlresolvers import reverse
from rest_framework import status
import api.messages as messages
from api.models import (Credential,
                        Source,
                        ScanTask,
                        ScanJob,
                        ConnectionResults,
                        ConnectionResult,
                        SystemConnectionResult,
                        InspectionResults,
                        InspectionResult,
                        SystemInspectionResult,
                        RawFact)
from api.scanjob.view import (expand_scanjob,
                              expand_sys_conn_result,
                              expand_conn_results,
                              expand_inspect_results)


def dummy_start():
    """Create a dummy method for testing."""
    pass


# pylint: disable=unused-argument,invalid-name
class ScanJobTest(TestCase):
    """Test the basic ScanJob infrastructure."""

    def setUp(self):
        """Create test setup."""
        self.cred = Credential.objects.create(
            name='cred1',
            username='username',
            password='password',
            become_password=None,
            ssh_keyfile=None)
        self.cred_for_upload = self.cred.id

        self.source = Source(
            name='source1',
            source_type='network',
            port=22)
        self.source.save()
        self.source.credentials.add(self.cred)

    def create(self, data):
        """Call the create endpoint."""
        url = reverse('scanjob-list')
        return self.client.post(url,
                                json.dumps(data),
                                'application/json')

    def create_expect_400(self, data, expected_response):
        """We will do a lot of create tests that expect HTTP 400s."""
        response = self.create(data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_json = response.json()
        self.assertEqual(response_json, expected_response)

    def create_expect_201(self, data):
        """Create a source, return the response as a dict."""
        response = self.create(data)
        response_json = response.json()
        if response.status_code != status.HTTP_201_CREATED:
            print('Cause of failure: ')
            print(response_json)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response_json

    def test_queue_task(self):
        """Test create queue state change."""
        scan_job = ScanJob(scan_type=ScanTask.SCAN_TYPE_INSPECT)
        scan_job.save()
        scan_job.sources.add(self.source)

        # Job in created state
        self.assertEqual(scan_job.status, ScanTask.CREATED)
        tasks = scan_job.tasks.all()
        self.assertEqual(len(tasks), 0)

        # Queue job to run
        scan_job.queue()

        # Job should be in pending state
        self.assertEqual(scan_job.status, ScanTask.PENDING)

        # Queue should have created scan tasks
        tasks = scan_job.tasks.all()
        self.assertEqual(len(tasks), 2)

        # Validate connect task created and correct
        connect_task = tasks[0]
        self.assertEqual(connect_task.scan_type, ScanTask.SCAN_TYPE_CONNECT)
        self.assertEqual(connect_task.status, ScanTask.PENDING)

        # Validate inspect task created and correct
        inspect_task = tasks[1]
        self.assertEqual(inspect_task.scan_type, ScanTask.SCAN_TYPE_INSPECT)
        self.assertEqual(inspect_task.status, ScanTask.PENDING)

    def test_queue_invalid_state_changes(self):
        """Test create queue failed."""
        scan_job = ScanJob(status=ScanTask.FAILED,
                           scan_type=ScanTask.SCAN_TYPE_INSPECT)
        scan_job.save()
        scan_job.sources.add(self.source)

        # Queue job to run
        scan_job.queue()
        self.assertEqual(scan_job.status, ScanTask.FAILED)

        scan_job.complete()
        self.assertEqual(scan_job.status, ScanTask.FAILED)

        scan_job.pause()
        self.assertEqual(scan_job.status, ScanTask.FAILED)

        scan_job.start()
        self.assertEqual(scan_job.status, ScanTask.FAILED)

        scan_job.cancel()
        self.assertEqual(scan_job.status, ScanTask.FAILED)

        scan_job.restart()
        self.assertEqual(scan_job.status, ScanTask.FAILED)

        scan_job.fail('test failure')
        self.assertEqual(scan_job.status, ScanTask.FAILED)

        scan_job.status = ScanTask.CREATED
        scan_job.fail('test failure')
        self.assertEqual(scan_job.status, ScanTask.CREATED)

        scan_job.status = ScanTask.RUNNING
        scan_job.complete()
        self.assertEqual(scan_job.status, ScanTask.COMPLETED)

    @patch('api.scanjob.view.start_scan', side_effect=dummy_start)
    def test_start_task(self, start_scan):
        """Test start pending task."""
        scan_job = ScanJob(scan_type=ScanTask.SCAN_TYPE_CONNECT)
        scan_job.save()
        scan_job.sources.add(self.source)

        # Job in created state
        tasks = scan_job.tasks.all()

        # Queue job to run
        scan_job.queue()
        self.assertEqual(scan_job.status, ScanTask.PENDING)

        # Queue should have created scan tasks
        tasks = scan_job.tasks.all()
        self.assertEqual(len(tasks), 1)

        # Start job
        scan_job.start()

    @patch('api.scanjob.view.start_scan', side_effect=dummy_start)
    def test_pause_restart_task(self, start_scan):
        """Test pause and restart task."""
        scan_job = ScanJob(scan_type=ScanTask.SCAN_TYPE_CONNECT)
        scan_job.save()
        scan_job.sources.add(self.source)

        # Job in created state
        tasks = scan_job.tasks.all()

        # Queue job to run
        scan_job.queue()
        self.assertEqual(scan_job.status, ScanTask.PENDING)

        # Queue should have created scan tasks
        tasks = scan_job.tasks.all()
        self.assertEqual(len(tasks), 1)
        connect_task = scan_job.tasks.first()
        self.assertEqual(connect_task.status, ScanTask.PENDING)

        # Start job
        scan_job.start()
        self.assertEqual(scan_job.status, ScanTask.RUNNING)

        scan_job.pause()
        connect_task = scan_job.tasks.first()
        self.assertEqual(scan_job.status, ScanTask.PAUSED)
        self.assertEqual(connect_task.status, ScanTask.PAUSED)

        scan_job.restart()
        connect_task = scan_job.tasks.first()
        self.assertEqual(scan_job.status, ScanTask.RUNNING)
        self.assertEqual(connect_task.status, ScanTask.PENDING)

        scan_job.cancel()
        connect_task = scan_job.tasks.first()
        self.assertEqual(scan_job.status, ScanTask.CANCELED)
        self.assertEqual(connect_task.status, ScanTask.CANCELED)

    @patch('api.scanjob.view.start_scan', side_effect=dummy_start)
    def test_successful_create(self, start_scan):
        """A valid create request should succeed."""
        data = {'sources': [self.source.id],
                'scan_type': ScanTask.SCAN_TYPE_CONNECT}
        response = self.create_expect_201(data)
        self.assertIn('id', response)

    def test_create_no_source(self):
        """A create request must have a source."""
        self.create_expect_400(
            {}, {'sources': ['This field is required.']})

    def test_create_invalid_scan_type(self):
        """A create request must have a valid scan_type."""
        data = {'sources': [self.source.id],
                'scan_type': 'foo',
                'options': {'disable_optional_products': {'jboss_eap': True,
                                                          'jboss_fuse': True,
                                                          'jboss_brms': True}}}
        self.create_expect_400(
            data, {'scan_type': ['foo, is an invalid choice. '
                                 'Valid values are connect,inspect.']})

    def test_create_blank_scan_type(self):
        """A create request must not have a blank scan_type."""
        data = {'sources': [self.source.id],
                'scan_type': ''}
        self.create_expect_400(
            data, {'scan_type': ['This field may not be blank. '
                                 'Valid values are connect,inspect.']})

    def test_create_invalid_srcs_type(self):
        """A create request must have integer ids."""
        data = {'sources': ['foo'],
                'scan_type': ScanTask.SCAN_TYPE_CONNECT}
        self.create_expect_400(
            data, {'sources': ['Source identitiers must be integer values.']})

    def test_create_invalid_srcs_id(self):
        """A create request must have vaild ids."""
        data = {'sources': [100000],
                'scan_type': ScanTask.SCAN_TYPE_CONNECT}
        self.create_expect_400(
            data, {'sources': ['Source with id=100000 could '
                               'not be found in database.']})

    @patch('api.scanjob.view.start_scan', side_effect=dummy_start)
    def test_create_default_host_type(self, start_scan):
        """A valid create request should succeed with defaulted type."""
        data = {'sources': [self.source.id],
                'options': {'disable_optional_products': {'jboss_eap': True,
                                                          'jboss_fuse': True,
                                                          'jboss_brms': True}}}
        response = self.create_expect_201(data)
        self.assertIn('id', response)
        self.assertIn('scan_type', response)
        self.assertEqual(response['scan_type'], ScanTask.SCAN_TYPE_INSPECT)

    def test_create_invalid_source(self):
        """The Source name must valid."""
        self.create_expect_400(
            {'sources': -1},
            {'sources':
             ['Expected a list of items but got type "int".']})

    def test_create_invalid_forks(self):
        """Test valid number of forks."""
        data = {'sources': [self.source.id],
                'options': {'max_concurrency': -5}}
        self.create_expect_400(data, {
            'options': {'max_concurrency':
                        ['Ensure this value is greater than or equal '
                         'to 1.']}})

    @patch('api.scanjob.view.start_scan', side_effect=dummy_start)
    def test_list(self, start_scan):
        """List all ScanJob objects."""
        data_default = {'sources': [self.source.id],
                        'options': {'disable_optional_products':
                                    {'jboss_eap': True,
                                     'jboss_fuse': True,
                                     'jboss_brms': True}}}
        data_discovery = {'sources': [self.source.id],
                          'scan_type': ScanTask.SCAN_TYPE_CONNECT,
                          'options': {'disable_optional_products':
                                      {'jboss_eap': True,
                                       'jboss_fuse': True,
                                       'jboss_brms': True}}}
        self.create_expect_201(data_default)
        self.create_expect_201(data_discovery)

        url = reverse('scanjob-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        content = response.json()
        expected = [{'id': 1,
                     'options': {'max_concurrency': 50,
                                 'disable_optional_products':
                                     {'jboss_eap': True,
                                      'jboss_fuse': True,
                                      'jboss_brms': True}},
                     'sources': [{'id': 1, 'name': 'source1',
                                  'source_type': 'network'}],
                     'scan_type': ScanTask.SCAN_TYPE_INSPECT,
                     'status': 'created',
                     'status_message': messages.SJ_STATUS_MSG_CREATED},
                    {'id': 2,
                     'options': {'max_concurrency': 50,
                                 'disable_optional_products':
                                     {'jboss_eap': True,
                                      'jboss_fuse': True,
                                      'jboss_brms': True}},
                     'sources': [{'id': 1, 'name': 'source1',
                                  'source_type': 'network'}],
                     'scan_type': ScanTask.SCAN_TYPE_CONNECT,
                     'status': 'created',
                     'status_message': messages.SJ_STATUS_MSG_CREATED}]
        self.assertEqual(content, expected)

    @patch('api.scanjob.view.start_scan', side_effect=dummy_start)
    def test_filtered_list(self, start_scan):
        """List filtered ScanJob objects."""
        data_default = {'sources': [self.source.id],
                        'options': {'disable_optional_products':
                                    {'jboss_eap': True,
                                     'jboss_fuse': True,
                                     'jboss_brms': True}}}
        data_discovery = {'sources': [self.source.id],
                          'scan_type': ScanTask.SCAN_TYPE_CONNECT,
                          'options': {'disable_optional_products':
                                      {'jboss_eap': True,
                                       'jboss_fuse': True,
                                       'jboss_brms': True}}}
        self.create_expect_201(data_default)
        self.create_expect_201(data_discovery)

        url = reverse('scanjob-list')
        response = self.client.get(
            url, {'scan_type': ScanTask.SCAN_TYPE_CONNECT})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        content = response.json()
        expected = [{'id': 2,
                     'options': {'max_concurrency': 50,
                                 'disable_optional_products':
                                     {'jboss_eap': True,
                                      'jboss_fuse': True,
                                      'jboss_brms': True}},
                     'sources': [{'id': 1, 'name': 'source1',
                                  'source_type': 'network'}],
                     'scan_type': ScanTask.SCAN_TYPE_CONNECT,
                     'status': 'created',
                     'status_message': messages.SJ_STATUS_MSG_CREATED}]
        self.assertEqual(content, expected)

        response = self.client.get(
            url, {'status': ScanTask.PENDING})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        content = response.json()
        expected = []
        self.assertEqual(content, expected)

        response = self.client.get(
            url, {'status': ScanTask.CREATED})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        content = response.json()
        expected = [{'id': 1,
                     'options': {'max_concurrency': 50,
                                 'disable_optional_products':
                                     {'jboss_eap': True,
                                      'jboss_fuse': True,
                                      'jboss_brms': True}},
                     'sources': [{'id': 1, 'name': 'source1',
                                  'source_type': 'network'}],
                     'scan_type': ScanTask.SCAN_TYPE_INSPECT,
                     'status': 'created',
                     'status_message': messages.SJ_STATUS_MSG_CREATED},
                    {'id': 2,
                     'options': {'max_concurrency': 50,
                                 'disable_optional_products':
                                     {'jboss_eap': True,
                                      'jboss_fuse': True,
                                      'jboss_brms': True}},
                     'sources': [{'id': 1, 'name': 'source1',
                                  'source_type': 'network'}],
                     'scan_type': ScanTask.SCAN_TYPE_CONNECT,
                     'status': 'created',
                     'status_message': messages.SJ_STATUS_MSG_CREATED}]
        self.assertEqual(content, expected)

    @patch('api.scanjob.view.start_scan', side_effect=dummy_start)
    def test_retrieve(self, start_scan):
        """Get ScanJob details by primary key."""
        data_discovery = {'sources': [self.source.id],
                          'scan_type': ScanTask.SCAN_TYPE_CONNECT,
                          'options': {'disable_optional_products':
                                      {'jboss_eap': True,
                                       'jboss_fuse': True,
                                       'jboss_brms': True}}}
        initial = self.create_expect_201(data_discovery)

        url = reverse('scanjob-detail', args=(initial['id'],))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('sources', response.json())
        sources = response.json()['sources']

        self.assertEqual(
            sources, [{'id': 1, 'name': 'source1', 'source_type': 'network'}])

    @patch('api.scanjob.view.start_scan', side_effect=dummy_start)
    def test_details(self, start_scan):
        """Get ScanJob result details by primary key."""
        scan_job = ScanJob(scan_type=ScanTask.SCAN_TYPE_INSPECT)
        scan_job.save()
        scan_job.sources.add(self.source)

        # Job in created state
        self.assertEqual(scan_job.status, ScanTask.CREATED)
        tasks = scan_job.tasks.all()
        self.assertEqual(len(tasks), 0)

        # Queue job to run
        scan_job.queue()

        conn_task = scan_job.tasks.first()

        conn_results = ConnectionResults(scan_job=scan_job)
        conn_results.save()

        conn_result = ConnectionResult(
            source=conn_task.source, scan_task=conn_task)
        conn_result.save()

        conn_results.results.add(conn_result)
        conn_results.save()

        sys_result = SystemConnectionResult(name='Foo',
                                            credential=self.cred,
                                            status=SystemConnectionResult
                                            .SUCCESS)
        sys_result.save()
        conn_result.systems.add(sys_result)
        conn_result.save()

        inspect_task = scan_job.tasks.all()[1]

        inspect_results = InspectionResults(scan_job=scan_job)
        inspect_results.save()

        inspect_result = InspectionResult(
            source=inspect_task.source, scan_task=inspect_task)
        inspect_result.save()

        inspect_results.results.add(inspect_result)
        inspect_results.save()

        sys_result = SystemInspectionResult(name='Foo',
                                            status=SystemConnectionResult
                                            .SUCCESS)
        sys_result.save()

        fact = RawFact(name='foo', value='value')
        fact.save()
        sys_result.facts.add(fact)
        sys_result.save()

        inspect_result.systems.add(sys_result)
        inspect_result.save()

        url = reverse('scanjob-detail', args=(scan_job.id,)) + 'results/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        self.assertIn('connection_results', json_response)
        self.assertIn('inspection_results', json_response)

        self.assertEqual(
            json_response, {'connection_results':
                            {'scan_job': 1, 'results': []},
                            'inspection_results': {'scan_job': 1,
                                                   'results': []}})

    @patch('api.scanjob.view.start_scan', side_effect=dummy_start)
    def test_update_not_allowed(self, start_scan):
        """Completely update a Source."""
        data_discovery = {'sources': [self.source.id],
                          'scan_type': ScanTask.SCAN_TYPE_CONNECT,
                          'options': {'disable_optional_products':
                                      {'jboss_eap': True,
                                       'jboss_fuse': True,
                                       'jboss_brms': True}}}
        initial = self.create_expect_201(data_discovery)

        data = {'sources': [self.source.id],
                'scan_type': ScanTask.SCAN_TYPE_INSPECT,
                'options': {'disable_optional_products':
                            {'jboss_eap': True,
                             'jboss_fuse': True,
                             'jboss_brms': True}}}
        url = reverse('scanjob-detail', args=(initial['id'],))
        response = self.client.put(url,
                                   json.dumps(data),
                                   content_type='application/json',
                                   format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    @patch('api.scanjob.view.start_scan', side_effect=dummy_start)
    def test_partial_update(self, start_scan):
        """Partially update a ScanJob is not supported."""
        data_discovery = {'sources': [self.source.id],
                          'scan_type': ScanTask.SCAN_TYPE_CONNECT,
                          'options': {'disable_optional_products':
                                      {'jboss_eap': True,
                                       'jboss_fuse': True,
                                       'jboss_brms': True}}}
        initial = self.create_expect_201(data_discovery)

        data = {'scan_type': ScanTask.SCAN_TYPE_INSPECT}
        url = reverse('scanjob-detail', args=(initial['id'],))
        response = self.client.patch(url,
                                     json.dumps(data),
                                     content_type='application/json',
                                     format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    @patch('api.scanjob.view.start_scan', side_effect=dummy_start)
    def test_delete(self, start_scan):
        """Delete a ScanJob is not supported."""
        data_discovery = {'sources': [self.source.id],
                          'scan_type': ScanTask.SCAN_TYPE_CONNECT,
                          'options': {'disable_optional_products':
                                      {'jboss_eap': True,
                                       'jboss_fuse': True,
                                       'jboss_brms': True}}}
        response = self.create_expect_201(data_discovery)

        url = reverse('scanjob-detail', args=(response['id'],))
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    @patch('api.scanjob.view.start_scan', side_effect=dummy_start)
    def test_pause_bad_state(self, start_scan):
        """Pause a scanjob."""
        data_host = {'sources': [self.source.id],
                     'scan_type': ScanTask.SCAN_TYPE_INSPECT,
                     'options': {'disable_optional_products':
                                 {'jboss_eap': True,
                                  'jboss_fuse': True,
                                  'jboss_brms': True}}}

        response = self.create_expect_201(data_host)

        url = reverse('scanjob-detail', args=(response['id'],))
        pause_url = '{}pause/'.format(url)
        response = self.client.put(pause_url, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST)

    @patch('api.scanjob.view.start_scan', side_effect=dummy_start)
    def test_cancel(self, start_scan):
        """Cancel a scanjob."""
        data_host = {'sources': [self.source.id],
                     'scan_type': ScanTask.SCAN_TYPE_INSPECT,
                     'options': {'disable_optional_products':
                                 {'jboss_eap': True,
                                  'jboss_fuse': True,
                                  'jboss_brms': True}}}
        response = self.create_expect_201(data_host)

        url = reverse('scanjob-detail', args=(response['id'],))
        pause_url = '{}cancel/'.format(url)
        response = self.client.put(pause_url, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK)

    @patch('api.scanjob.view.start_scan', side_effect=dummy_start)
    def test_restart_bad_state(self, start_scan):
        """Restart a scanjob."""
        data_host = {'sources': [self.source.id],
                     'scan_type': ScanTask.SCAN_TYPE_INSPECT,
                     'options': {'disable_optional_products':
                                 {'jboss_eap': True,
                                  'jboss_fuse': True,
                                  'jboss_brms': True}}}
        response = self.create_expect_201(data_host)

        url = reverse('scanjob-detail', args=(response['id'],))
        pause_url = '{}restart/'.format(url)
        response = self.client.put(pause_url, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST)

    def test_expand_scanjob(self):
        """Test view expand_scanjob."""
        scan_job = ScanJob(scan_type=ScanTask.SCAN_TYPE_INSPECT)
        scan_job.save()
        scan_job.sources.add(self.source)

        # Job in created state
        self.assertEqual(scan_job.status, ScanTask.CREATED)
        tasks = scan_job.tasks.all()
        self.assertEqual(len(tasks), 0)

        # Queue job to run
        scan_job.queue()
        task = scan_job.tasks.all()[1]
        task.systems_count = 2
        task.systems_failed = 1
        task.systems_scanned = 1
        task.save()

        scan_job = ScanJob.objects.filter(pk=scan_job.id).first()

        json_scan = {'tasks': [{}]}
        expand_scanjob(scan_job, json_scan)

        self.assertEqual(json_scan.get('systems_count'), 2)
        self.assertEqual(json_scan.get('systems_failed'), 1)
        self.assertEqual(json_scan.get('systems_scanned'), 1)

    def test_expand_sys_conn_result(self):
        """Test view expand_sys_conn_result."""
        scan_job = ScanJob(scan_type=ScanTask.SCAN_TYPE_CONNECT)
        scan_job.save()
        scan_job.sources.add(self.source)

        # Job in created state
        self.assertEqual(scan_job.status, ScanTask.CREATED)
        tasks = scan_job.tasks.all()
        self.assertEqual(len(tasks), 0)

        # Queue job to run
        scan_job.queue()

        conn_task = scan_job.tasks.first()

        conn_result = ConnectionResult(
            source=conn_task.source, scan_task=conn_task)
        conn_result.save()

        sys_result = SystemConnectionResult(name='Foo',
                                            credential=self.cred,
                                            status=SystemConnectionResult
                                            .SUCCESS)
        sys_result.save()
        conn_result.systems.add(sys_result)
        conn_result.save()

        result = expand_sys_conn_result(conn_result)
        self.assertEqual(result[0]['credential']['name'], 'cred1')

    def test_expand_conn_results(self):
        """Test view expand_conn_results."""
        scan_job = ScanJob(scan_type=ScanTask.SCAN_TYPE_CONNECT)
        scan_job.save()
        scan_job.sources.add(self.source)

        # Job in created state
        self.assertEqual(scan_job.status, ScanTask.CREATED)
        tasks = scan_job.tasks.all()
        self.assertEqual(len(tasks), 0)

        # Queue job to run
        scan_job.queue()

        conn_task = scan_job.tasks.first()

        conn_results = ConnectionResults(scan_job=scan_job)
        conn_results.save()

        conn_result = ConnectionResult(
            source=conn_task.source, scan_task=conn_task)
        conn_result.save()

        conn_results.results.add(conn_result)
        conn_results.save()

        sys_result = SystemConnectionResult(name='Foo',
                                            credential=self.cred,
                                            status=SystemConnectionResult
                                            .SUCCESS)
        sys_result.save()
        conn_result.systems.add(sys_result)
        conn_result.save()

        conn_results_json = {'results': [{}]}
        expand_conn_results(conn_results, conn_results_json)
        self.assertEqual(
            conn_results_json['results'][0]['systems'][0]['name'], 'Foo')

    def test_expand_inspect_results(self):
        """Test view expand_inspect_results."""
        scan_job = ScanJob(scan_type=ScanTask.SCAN_TYPE_INSPECT)
        scan_job.save()
        scan_job.sources.add(self.source)

        # Job in created state
        self.assertEqual(scan_job.status, ScanTask.CREATED)
        tasks = scan_job.tasks.all()
        self.assertEqual(len(tasks), 0)

        # Queue job to run
        scan_job.queue()

        inspect_task = scan_job.tasks.all()[1]

        inspect_results = InspectionResults(scan_job=scan_job)
        inspect_results.save()

        inspect_result = InspectionResult(
            source=inspect_task.source, scan_task=inspect_task)
        inspect_result.save()

        inspect_results.results.add(inspect_result)
        inspect_results.save()

        sys_result = SystemInspectionResult(name='Foo',
                                            status=SystemConnectionResult
                                            .SUCCESS)
        sys_result.save()

        fact = RawFact(name='foo', value='"value"')
        fact.save()
        sys_result.facts.add(fact)
        sys_result.save()

        inspect_result.systems.add(sys_result)
        inspect_result.save()

        inspect_results_json = {'results': [{}]}
        expand_inspect_results(inspect_results, inspect_results_json)
        self.assertEqual(
            inspect_results_json['results'][0]['systems'][0]
            ['facts'][0]['name'],
            'foo')
