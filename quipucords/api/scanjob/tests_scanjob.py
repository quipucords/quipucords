#
# Copyright (c) 2017-2018 Red Hat, Inc.
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
from api.scanjob.serializer import (ScanJobSerializer)
from api.models import (Credential,
                        Source,
                        ScanTask,
                        Scan,
                        ExtendedProductSearchOptions,
                        ScanOptions,
                        ScanJob,
                        SystemConnectionResult,
                        SystemInspectionResult,
                        RawFact)
from api.scanjob.view import (expand_scanjob,
                              expand_sys_conn_result,
                              expand_conn_results,
                              expand_inspect_results)
from scanner.test_util import create_scan_job


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

        self.connect_scan = Scan(name='connect_test',
                                 scan_type=ScanTask.SCAN_TYPE_CONNECT)
        self.connect_scan.save()
        self.connect_scan.sources.add(self.source)
        self.connect_scan.save()

        self.inspect_scan = Scan(name='inspect_test')
        self.inspect_scan.save()
        self.inspect_scan.sources.add(self.source)
        self.inspect_scan.save()

    def create_job_expect_201(self, scan_id):
        """Create a scan, return the response as a dict."""
        url = reverse('scan-detail', args=(scan_id,)) + 'jobs/'
        response = self.client.post(url,
                                    {},
                                    'application/json')
        response_json = response.json()
        if response.status_code != status.HTTP_201_CREATED:
            print('Cause of failure: ')
            print(response_json)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response_json

    def test_queue_task(self):
        """Test create queue state change."""
        # Cannot use util because its testing queue
        # Create scan configuration
        scan = Scan(name='test',
                    scan_type=ScanTask.SCAN_TYPE_INSPECT)
        scan.save()

        # Add source to scan
        scan.sources.add(self.source)

        options_to_use = ScanOptions()
        options_to_use.save()

        scan.options = options_to_use
        scan.save()

        # Create Job
        scan_job = ScanJob(scan=scan)
        scan_job.save()

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
        scan_job, _ = create_scan_job(
            self.source, scan_type=ScanTask.SCAN_TYPE_INSPECT)
        scan_job.status = ScanTask.FAILED

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

    def test_start_task(self):
        """Test start pending task."""
        scan_job, _ = create_scan_job(
            self.source, scan_type=ScanTask.SCAN_TYPE_CONNECT)

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

    def test_pause_restart_task(self):
        """Test pause and restart task."""
        scan_job, _ = create_scan_job(
            self.source, scan_type=ScanTask.SCAN_TYPE_CONNECT)

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

    @patch('api.scan.view.start_scan', side_effect=dummy_start)
    def test_successful_create(self, start_scan):
        """A valid create request should succeed."""
        response = self.create_job_expect_201(self.connect_scan.id)
        self.assertIn('id', response)

    @patch('api.scan.view.start_scan', side_effect=dummy_start)
    def test_retrieve(self, start_scan):
        """Get ScanJob details by primary key."""
        initial = self.create_job_expect_201(self.connect_scan.id)

        url = reverse('scanjob-detail', args=(initial['id'],))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('scan', response.json())
        scan = response.json()['scan']

        self.assertEqual(
            scan, {'id': 1, 'name': 'connect_test'})

    def test_retrieve_bad_id(self):
        """Get ScanJob details by bad primary key."""
        url = reverse('scanjob-detail', args=('string',))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_details(self):
        """Get ScanJob result details by primary key."""
        # pylint: disable=no-member
        scan_job, scan_task = create_scan_job(
            self.source, ScanTask.SCAN_TYPE_INSPECT)

        # Create a connection system result
        sys_result = SystemConnectionResult(name='Foo',
                                            credential=self.cred,
                                            status=SystemConnectionResult
                                            .SUCCESS)
        sys_result.save()
        conn_result = scan_task.prerequisites.first().connection_result
        conn_result.systems.add(sys_result)
        conn_result.save()

        # Create an inspection system result
        sys_result = SystemInspectionResult(name='Foo',
                                            status=SystemConnectionResult
                                            .SUCCESS)
        sys_result.save()

        fact = RawFact(name='fact_key', value='"fact_value"')
        fact.save()
        sys_result.facts.add(fact)
        sys_result.save()

        inspect_result = scan_task.inspection_result
        inspect_result.systems.add(sys_result)
        inspect_result.save()
        scan_job.save()

        url = reverse('scanjob-detail', args=(scan_job.id,)) + 'results/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        self.assertIn('connection_results', json_response)
        self.assertIn('inspection_results', json_response)

        self.assertEqual(
            json_response, {
                'connection_results': {'task_results': [
                    {'source':
                     {'id': 1, 'name': 'source1', 'source_type': 'network'},
                     'systems':
                     [{'name': 'Foo', 'credential':
                       {'id': 1, 'name': 'cred1'},
                       'status': 'success'}]}]},
                'inspection_results': {'task_results': [
                    {'source':
                     {'id': 1, 'name': 'source1', 'source_type': 'network'},
                     'systems':
                     [{'name': 'Foo', 'status': 'success',
                       'facts': [
                           {'name': 'fact_key', 'value': 'fact_value'}]}]}]}})

    def test_post_jobs_not_allowed(self):
        """Test post jobs not allowed."""
        url = reverse('scanjob-detail', args=(1,))
        url = url[:-2]
        response = self.client.post(url,
                                    {},
                                    'application/json')
        self.assertEqual(response.status_code,
                         status.HTTP_404_NOT_FOUND)

    def test_list_not_allowed(self):
        """Test list all jobs not allowed."""
        url = reverse('scanjob-detail', args=(1,))
        url = url[:-2]
        response = self.client.get(url,
                                   format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_404_NOT_FOUND)

    @patch('api.scan.view.start_scan', side_effect=dummy_start)
    def test_update_not_allowed(self, start_scan):
        """Test update scanjob not allowed."""
        initial = self.create_job_expect_201(self.connect_scan.id)

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

    @patch('api.scan.view.start_scan', side_effect=dummy_start)
    def test_update_not_allowed_disable_optional_products(self, start_scan):
        """Test update scan job options not allowed."""
        initial = self.create_job_expect_201(self.connect_scan.id)

        data = {'sources': [self.source.id],
                'scan_type': ScanTask.SCAN_TYPE_INSPECT,
                'options': {'disable_optional_products': 'bar'}}
        url = reverse('scanjob-detail', args=(initial['id'],))
        response = self.client.put(url,
                                   json.dumps(data),
                                   content_type='application/json',
                                   format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    @patch('api.scan.view.start_scan', side_effect=dummy_start)
    def test_partial_update(self, start_scan):
        """Test partial update not allow for scanjob."""
        initial = self.create_job_expect_201(self.connect_scan.id)

        data = {'scan_type': ScanTask.SCAN_TYPE_INSPECT}
        url = reverse('scanjob-detail', args=(initial['id'],))
        response = self.client.patch(url,
                                     json.dumps(data),
                                     content_type='application/json',
                                     format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    @patch('api.scan.view.start_scan', side_effect=dummy_start)
    def test_delete(self, start_scan):
        """Delete a ScanJob is not supported."""
        initial = self.create_job_expect_201(self.connect_scan.id)

        url = reverse('scanjob-detail', args=(initial['id'],))
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    @patch('api.scan.view.start_scan', side_effect=dummy_start)
    def test_pause_bad_state(self, start_scan):
        """Pause a scanjob."""
        initial = self.create_job_expect_201(self.connect_scan.id)

        url = reverse('scanjob-detail', args=(initial['id'],))
        pause_url = '{}pause/'.format(url)
        response = self.client.put(pause_url, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST)

    def test_pause_bad_id(self):
        """Pause a scanjob with bad id."""
        url = reverse('scanjob-detail', args=('string',))
        pause_url = '{}pause/'.format(url)
        response = self.client.put(pause_url, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST)

    @patch('api.scan.view.start_scan', side_effect=dummy_start)
    def test_cancel(self, start_scan):
        """Cancel a scanjob."""
        initial = self.create_job_expect_201(self.connect_scan.id)

        url = reverse('scanjob-detail', args=(initial['id'],))
        pause_url = '{}cancel/'.format(url)
        response = self.client.put(pause_url, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK)

    def test_cancel_bad_id(self):
        """Cancel a scanjob with bad id."""
        url = reverse('scanjob-detail', args=('string',))
        pause_url = '{}cancel/'.format(url)
        response = self.client.put(pause_url, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST)

    @patch('api.scan.view.start_scan', side_effect=dummy_start)
    def test_restart_bad_state(self, start_scan):
        """Restart a scanjob."""
        initial = self.create_job_expect_201(self.connect_scan.id)

        url = reverse('scanjob-detail', args=(initial['id'],))
        pause_url = '{}restart/'.format(url)
        response = self.client.put(pause_url, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST)

    def test_restart_bad_id(self):
        """Restart a scanjob with bad id."""
        url = reverse('scanjob-detail', args=('string',))
        pause_url = '{}restart/'.format(url)
        response = self.client.put(pause_url, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST)

    def test_expand_scanjob(self):
        """Test view expand_scanjob."""
        scan_job, scan_task = create_scan_job(
            self.source, scan_type=ScanTask.SCAN_TYPE_INSPECT)
        scan_task.update_stats('TEST_VC.', sys_count=2,
                               sys_failed=1, sys_scanned=1)

        scan_job = ScanJob.objects.filter(pk=scan_job.id).first()
        serializer = ScanJobSerializer(scan_job)
        json_scan = serializer.data
        json_scan = expand_scanjob(json_scan)

        self.assertEqual(json_scan.get('systems_count'), 2)
        self.assertEqual(json_scan.get('systems_failed'), 1)
        self.assertEqual(json_scan.get('systems_scanned'), 1)

    def test_expand_sys_conn_result(self):
        """Test view expand_sys_conn_result."""
        # pylint: disable=no-member
        _, scan_task = create_scan_job(
            self.source, ScanTask.SCAN_TYPE_CONNECT)

        sys_result = SystemConnectionResult(name='Foo',
                                            credential=self.cred,
                                            status=SystemConnectionResult
                                            .SUCCESS)
        sys_result.save()
        conn_result = scan_task.connection_result
        conn_result.systems.add(sys_result)
        conn_result.save()

        result = expand_sys_conn_result(conn_result)
        self.assertEqual(result[0]['credential']['name'], 'cred1')

    def test_expand_conn_results(self):
        """Test view expand_conn_results."""
        # pylint: disable=no-member
        scan_job, scan_task = create_scan_job(
            self.source, ScanTask.SCAN_TYPE_CONNECT)

        sys_result = SystemConnectionResult(name='Foo',
                                            credential=self.cred,
                                            status=SystemConnectionResult
                                            .SUCCESS)
        sys_result.save()
        conn_result = scan_task.connection_result
        conn_result.systems.add(sys_result)
        conn_result.save()

        conn_results_json = {'task_results': [{}]}
        expand_conn_results(scan_job.connection_results, conn_results_json)
        self.assertEqual(
            conn_results_json['task_results'][0]['systems'][0]['name'], 'Foo')

    def test_expand_inspect_results(self):
        """Test view expand_inspect_results."""
        # pylint: disable=no-member
        scan_job, scan_task = create_scan_job(self.source,
                                              ScanTask.SCAN_TYPE_INSPECT)

        sys_result = SystemInspectionResult(name='Foo',
                                            status=SystemConnectionResult
                                            .SUCCESS)
        sys_result.save()

        fact = RawFact(name='foo', value='"value"')
        fact.save()

        sys_result.facts.add(fact)
        sys_result.save()

        inspect_result = scan_task.inspection_result
        inspect_result.systems.add(sys_result)
        inspect_result.save()

        inspect_results_json = {'task_results': [{}]}
        expand_inspect_results(
            scan_job.inspection_results, inspect_results_json)
        self.assertEqual(
            inspect_results_json['task_results'][0]['systems'][0]
            ['facts'][0]['name'],
            'foo')

    def test_get_extra_vars(self):
        """Tests the get_extra_vars method with empty dict."""
        extended = ExtendedProductSearchOptions()
        extended.save()
        scan_options = ScanOptions(enable_extended_product_search=extended)
        scan_options.disable_optional_products = {}
        scan_options.save()
        scan_job, _ = create_scan_job(self.source,
                                      ScanTask.SCAN_TYPE_INSPECT,
                                      scan_options=scan_options)
        extra_vars = scan_job.options.get_extra_vars()

        expected_vars = {'jboss_eap': True,
                         'jboss_fuse': True,
                         'jboss_brms': True,
                         'jboss_eap_ext': False,
                         'jboss_fuse_ext': False,
                         'jboss_brms_ext': False}
        self.assertEqual(extra_vars, expected_vars)

    def test_get_extra_vars_extended_search(self):
        """Tests the get_extra_vars method with extended search."""
        extended = ExtendedProductSearchOptions(
            jboss_eap=True,
            jboss_fuse=True,
            jboss_brms=True,
            search_directories='["a", "b"]')
        extended.save()
        scan_options = ScanOptions(enable_extended_product_search=extended)
        scan_options.disable_optional_products = {}
        scan_options.save()
        scan_job, _ = create_scan_job(self.source,
                                      ScanTask.SCAN_TYPE_INSPECT,
                                      scan_options=scan_options)
        extra_vars = scan_job.options.get_extra_vars()

        expected_vars = {'jboss_eap': True,
                         'jboss_fuse': True,
                         'jboss_brms': True,
                         'jboss_eap_ext': True,
                         'jboss_fuse_ext': True,
                         'jboss_brms_ext': True,
                         'search_directories': 'a b'}
        self.assertEqual(extra_vars, expected_vars)

    def test_get_extra_vars_mixed(self):
        """Tests the get_extra_vars method with mixed values."""
        extended = ExtendedProductSearchOptions()
        extended.save()
        scan_options = ScanOptions(enable_extended_product_search=extended)
        scan_options.disable_optional_products = {'jboss_eap': False,
                                                  'jboss_fuse': False,
                                                  'jboss_brms': True}
        scan_options.save()

        scan_job, _ = create_scan_job(self.source,
                                      ScanTask.SCAN_TYPE_INSPECT,
                                      scan_options=scan_options)
        extra_vars = scan_job.options.get_extra_vars()

        expected_vars = {'jboss_eap': True,
                         'jboss_fuse': False,
                         'jboss_brms': True,
                         'jboss_eap_ext': False,
                         'jboss_fuse_ext': False,
                         'jboss_brms_ext': False}
        self.assertEqual(extra_vars, expected_vars)

    def test_get_extra_vars_false(self):
        """Tests the get_extra_vars method with all False."""
        extended = ExtendedProductSearchOptions()
        extended.save()
        scan_options = ScanOptions(enable_extended_product_search=extended)
        scan_options.disable_optional_products = {'jboss_eap': False,
                                                  'jboss_fuse': False,
                                                  'jboss_brms': False}
        scan_options.save()

        scan_job, _ = create_scan_job(self.source,
                                      ScanTask.SCAN_TYPE_INSPECT,
                                      scan_options=scan_options)

        extra_vars = scan_job.options.get_extra_vars()

        expected_vars = {'jboss_eap': False,
                         'jboss_fuse': False,
                         'jboss_brms': False,
                         'jboss_eap_ext': False,
                         'jboss_fuse_ext': False,
                         'jboss_brms_ext': False}
        self.assertEqual(extra_vars, expected_vars)

    # ############################################################
    # # Scan Job tests /jobs path
    # ############################################################
    @patch('api.scan.view.start_scan', side_effect=dummy_start)
    def test_list_jobs(self, start_scan):
        """List all ScanJobs under a scan."""
        self.create_job_expect_201(self.inspect_scan.id)
        self.create_job_expect_201(self.connect_scan.id)

        url = reverse('scan-detail', args=(self.inspect_scan.id,)) + 'jobs/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        content = response.json()
        results1 = [{'id': 1,
                     'scan': {'id': 2, 'name': 'inspect_test'},
                     'scan_type': ScanTask.SCAN_TYPE_INSPECT,
                     'status': 'created',
                     'status_message': messages.SJ_STATUS_MSG_CREATED}]
        expected = {'count': 1,
                    'next': None,
                    'previous': None,
                    'results': results1}
        self.assertEqual(content, expected)

    @patch('api.scan.view.start_scan', side_effect=dummy_start)
    def test_filtered_list(self, start_scan):
        """List filtered ScanJob objects."""
        self.create_job_expect_201(self.inspect_scan.id)

        url = reverse('scan-detail', args=(self.inspect_scan.id,)) + 'jobs/'

        response = self.client.get(
            url, {'status': ScanTask.PENDING})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        content = response.json()
        expected = {'count': 0, 'next': None,
                    'previous': None, 'results': []}
        self.assertEqual(content, expected)

        response = self.client.get(
            url, {'status': ScanTask.CREATED})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        content = response.json()
        results1 = [{'id': 1,
                     'scan': {'id': 2, 'name': 'inspect_test'},
                     'scan_type': ScanTask.SCAN_TYPE_INSPECT,
                     'status': 'created',
                     'status_message': messages.SJ_STATUS_MSG_CREATED}]
        expected = {'count': 1,
                    'next': None,
                    'previous': None,
                    'results': results1}
        self.assertEqual(content, expected)

    @patch('api.scan.view.start_scan', side_effect=dummy_start)
    def test_delete_scan_cascade(self, start_scan):
        """Delete a scan and its related data."""
        # pylint: disable=no-member
        scan_job, scan_task = create_scan_job(
            self.source, ScanTask.SCAN_TYPE_INSPECT)

        scan = scan_job.scan
        scan_id = scan.id

        self.create_job_expect_201(scan_id)

        # Create a connection system result
        sys_result = SystemConnectionResult(name='Foo',
                                            credential=self.cred,
                                            status=SystemConnectionResult
                                            .SUCCESS)
        sys_result.save()
        conn_result = scan_task.prerequisites.first().connection_result
        conn_result.systems.add(sys_result)
        conn_result.save()

        # Create an inspection system result
        sys_result = SystemInspectionResult(name='Foo',
                                            status=SystemConnectionResult
                                            .SUCCESS)
        sys_result.save()

        fact = RawFact(name='fact_key', value='"fact_value"')
        fact.save()
        sys_result.facts.add(fact)
        sys_result.save()

        inspect_result = scan_task.inspection_result
        inspect_result.systems.add(sys_result)
        inspect_result.save()
        scan_job.save()

        job_count = len(scan.jobs.all())
        self.assertNotEqual(job_count, 0)
        url = reverse('scan-detail', args=(scan_id,))
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_204_NO_CONTENT)
        job_count = len(scan.jobs.all())
        self.assertEqual(job_count, 0)
