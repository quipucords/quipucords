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
"""ScanJobRunner runs a group of scan tasks."""
import logging
from multiprocessing import Process
from django.db.models import Q
from fingerprinter import pfc_signal
from api.fact.util import (validate_fact_collection_json,
                           build_sources_from_tasks,
                           get_or_create_fact_collection)
from api.models import (FactCollection,
                        ScanTask,
                        Source)
from scanner import network, vcenter, satellite


# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ScanJobRunner(Process):
    """ScanProcess perform a group of scan tasks."""

    def __init__(self, scan_job):
        """Create discovery scanner."""
        Process.__init__(self)
        self.scan_job = scan_job
        self.identifier = scan_job.id

    def run(self):
        """Trigger thread execution."""
        if self.scan_job.status == ScanTask.CREATED:
            # Job is not ready to run
            self.scan_job.queue()

        # Job is not running so start
        self.scan_job.start()

        # Load tasks that have no been run or are in progress
        task_runners = []
        incomplete_scan_tasks = self.scan_job.tasks.filter(
            Q(status=ScanTask.RUNNING) | Q(status=ScanTask.PENDING)
        ).order_by('sequence_number')
        task_info_message = ''
        for scan_task in incomplete_scan_tasks:
            task_info_message += str(scan_task.id) + ', '
            runner = self._create_task_runner(scan_task)
            if not runner:
                error_message = 'Scan task does not  have recognized '\
                    'type/source combination: %s' % scan_task

                scan_task.fail(error_message)
                self.scan_job.fail(error_message)
                return

            task_runners.append(runner)

        task_info_message = task_info_message[:-2]
        self.scan_job.log_message(
            'Queuing the following incomplete tasks: %s' % task_info_message)

        for runner in task_runners:
            # Mark runner as running
            runner.scan_task.start()

            # run runner
            try:
                status_message, task_status = runner.run()
            except Exception as error:
                message = 'FATAL ERROR. %s' % str(error)
                self.scan_job.fail(message)
                raise error

            # Save Task status
            if task_status == ScanTask.FAILED:
                runner.scan_task.fail(status_message)
            elif task_status == ScanTask.COMPLETED:
                runner.scan_task.complete(status_message)
            else:
                error_message = 'ScanTask %d failed.  Scan task must return '\
                    'ScanTask.COMPLETED or ScanTask.FAILED.  '\
                    'ScanTask returned %s' %\
                    (runner.scan_task.id, task_status)
                runner.scan_task.fail(error_message)

            if task_status != ScanTask.COMPLETED:
                # Task did not complete successfully so save job status as fail
                error_message = 'One of more tasks did not complete.  '\
                    'See tasks for details.'
                self.scan_job.fail(error_message)

        if self.scan_job.scan_type == ScanTask.SCAN_TYPE_INSPECT:
            self._send_facts_to_engine()

        # All tasks completed successfully and sent to endpoint
        if self.scan_job.status != ScanTask.FAILED:
            self.scan_job.complete()

        return self.scan_job.status

    def _create_task_runner(self, scan_task):
        """Create ScanTaskRunner using scan_type and source_type."""
        scan_type = scan_task.scan_type
        source_type = scan_task.source.source_type
        runner = None
        if (scan_type == ScanTask.SCAN_TYPE_CONNECT and
                source_type == Source.NETWORK_SOURCE_TYPE):
            runner = network.ConnectTaskRunner(
                self.scan_job, scan_task)
        elif (scan_type == ScanTask.SCAN_TYPE_CONNECT and
              source_type == Source.VCENTER_SOURCE_TYPE):
            runner = vcenter.ConnectTaskRunner(
                self.scan_job, scan_task)
        elif (scan_type == ScanTask.SCAN_TYPE_CONNECT and
              source_type == Source.SATELLITE_SOURCE_TYPE):
            runner = satellite.ConnectTaskRunner(
                self.scan_job, scan_task)
        elif (scan_type == ScanTask.SCAN_TYPE_INSPECT and
              source_type == Source.NETWORK_SOURCE_TYPE):
            runner = network.InspectTaskRunner(
                self.scan_job, scan_task)
        elif (scan_type == ScanTask.SCAN_TYPE_INSPECT and
              source_type == Source.VCENTER_SOURCE_TYPE):
            runner = vcenter.InspectTaskRunner(
                self.scan_job, scan_task)
        elif (scan_type == ScanTask.SCAN_TYPE_INSPECT and
              source_type == Source.SATELLITE_SOURCE_TYPE):
            runner = satellite.InspectTaskRunner(
                self.scan_job, scan_task)
        return runner

    def _send_facts_to_engine(self):
        """Send collected host scan facts to fact endpoint.

        :param facts: The array of fact dictionaries
        :returns: Identifer for the sent facts
        """
        inspect_tasks = self.scan_job.tasks.filter(
            scan_type=ScanTask.SCAN_TYPE_INSPECT).order_by('sequence_number')
        sources = build_sources_from_tasks(inspect_tasks.all())
        if bool(sources):
            fact_collection_json = {'sources': sources}
            has_errors, validation_result = validate_fact_collection_json(
                fact_collection_json)

            if has_errors:
                message = 'Scan producted invalid fact collection JSON: %s' % \
                    validation_result
                self.scan_job.fail(message)
                return

            # Create FC model and save data to JSON file
            fact_collection = get_or_create_fact_collection(
                fact_collection_json, scan_job=self.scan_job)

            # Send signal so fingerprint engine processes raw facts
            try:
                pfc_signal.send(sender=self.__class__,
                                instance=fact_collection)
                # Transition from persisted to complete after processing
                fact_collection.status = FactCollection.FC_STATUS_COMPLETE
                fact_collection.save()
                logger.debug(
                    'Fact collection %d successfully processed.',
                    fact_collection.id)
            except Exception as error:
                # Transition from persisted to failed after engine failed
                fact_collection.status = FactCollection.FC_STATUS_FAILED
                fact_collection.save()
                error_message = 'Fact collection %d failed'\
                    ' to be processed.' % fact_collection.id
                # Mark scanjob failed to avoid re-running on restart
                self.scan_job.fail(error_message)

                logger.error('%s:%s', error.__class__.__name__, error)
                raise error
        else:
            logger.error('No facts gathered from scan.')
            return None

    def __str__(self):
        """Convert to string."""
        return '{' + 'scan_job:{}, '.format(self.scan_job.id) + '}'
