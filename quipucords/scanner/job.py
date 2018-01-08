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
"""ScanJobRunner runs a group of scan tasks."""
import logging
from multiprocessing import Process
from django.db.models import Q
from fingerprinter import pfc_signal
from api.fact.util import (validate_fact_collection_json,
                           create_fact_collection,
                           ERRORS_KEY,
                           RESULT_KEY)
from api.models import (ScanTask, Source, ConnectionResults, InspectionResults)
from scanner import network, vcenter


# Get an instance of a logger
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ScanJobRunner(Process):
    """ScanProcess perform a group of scan tasks."""

    def __init__(self, scan_job):
        """Create discovery scanner."""
        Process.__init__(self)
        self.scan_job = scan_job
        self.identifier = scan_job.id
        self.conn_results = None
        self.inspect_results = None

    def run(self):
        """Trigger thread execution."""
        if self.scan_job.status == ScanTask.CREATED:
            # Job is not ready to run
            self.scan_job.queue()

        self.conn_results = ConnectionResults.objects.filter(
            scan_job=self.scan_job.id).first()
        self.inspect_results = InspectionResults.objects.filter(
            scan_job=self.scan_job.id).first()

        # Job is not running so start
        self.scan_job.start()

        # Load tasks that have no been run or are in progress
        task_runners = []
        incomplete_scan_tasks = self.scan_job.tasks.filter(
            Q(status=ScanTask.RUNNING) | Q(status=ScanTask.PENDING)
        ).order_by('sequence_number')
        for scan_task in incomplete_scan_tasks:
            runner = self._create_task_runner(scan_task)
            if not runner:
                logger.error(
                    'Scan Job failed.  Scan task does not'
                    ' have recognized type/source combination: %s',
                    scan_task)
                scan_task.status = ScanTask.FAILED
                self.scan_job.fail()
                return

            task_runners.append(runner)

        logger.info('ScanJob %s started', self.scan_job.id)

        for runner in task_runners:
            # Mark runner as running
            runner.scan_task.status = ScanTask.RUNNING
            runner.scan_task.save()

            logger.info('Running task: %s', runner)
            # run runner
            task_status = runner.run()

            # Save Task status
            runner.scan_task.status = task_status
            runner.scan_task.save()

            if task_status != ScanTask.COMPLETED:
                # Task did not complete successfully so save job status as fail
                self.scan_job.fail()

        if self.scan_job.scan_type == ScanTask.SCAN_TYPE_INSPECT:
            fact_collection_id = self._send_facts_to_engine()
            if not fact_collection_id:
                logger.error(
                    'Error: Facts not sent to fingerprint engine.  See logs.')
                self.scan_job.fail()
            else:
                self.scan_job.fact_collection_id = fact_collection_id

        # All tasks completed successfully and sent to endpoint
        if self.scan_job.status != ScanTask.FAILED:
            self.scan_job.complete()

        logger.info('ScanJob %s ended', self.scan_job.id)
        return self.scan_job.status

    def _create_task_runner(self, scan_task):
        """Create ScanTaskRunner using scan_type and source_type."""
        scan_type = scan_task.scan_type
        source_type = scan_task.source.source_type
        runner = None
        if (scan_type == ScanTask.SCAN_TYPE_CONNECT and
                source_type == Source.NETWORK_SOURCE_TYPE):
            runner = network.ConnectTaskRunner(
                self.scan_job, scan_task, self.conn_results)
        elif (scan_type == ScanTask.SCAN_TYPE_CONNECT and
              source_type == Source.VCENTER_SOURCE_TYPE):
            runner = vcenter.ConnectTaskRunner(
                self.scan_job, scan_task, self.conn_results)
        elif (scan_type == ScanTask.SCAN_TYPE_INSPECT and
              source_type == Source.NETWORK_SOURCE_TYPE):
            runner = network.InspectTaskRunner(
                self.scan_job, scan_task, self.inspect_results)
        elif (scan_type == ScanTask.SCAN_TYPE_INSPECT and
              source_type == Source.VCENTER_SOURCE_TYPE):
            runner = vcenter.InspectTaskRunner(
                self.scan_job, scan_task, self.inspect_results)
        return runner

    def _send_facts_to_engine(self):
        """Send collected host scan facts to fact endpoint.

        :param facts: The array of fact dictionaries
        :returns: Identifer for the sent facts
        """
        inspect_tasks = self.scan_job.tasks.filter(
            scan_type=ScanTask.SCAN_TYPE_INSPECT).filter(
                source__source_type=Source.NETWORK_SOURCE_TYPE).order_by(
                    'sequence_number')
        sources = []
        for inspect_task in inspect_tasks.all():
            runner = self._create_task_runner(inspect_task)
            if runner:
                task_facts = runner.get_facts()
                if task_facts:
                    source = inspect_task.source
                    source_dict = {'source_id': source.id,
                                   'source_type': source.source_type,
                                   'facts': task_facts}
                    sources.append(source_dict)

        if bool(sources):
            fact_collection_json = {'sources': sources}
            validation_result = validate_fact_collection_json(
                fact_collection_json)

            if validation_result[ERRORS_KEY]:
                logger.error('Scan producted invalid fact collection JSON: ')
                logger.error(validation_result[RESULT_KEY])
                return None

            # Create FC model and save data to JSON file
            fact_collection = create_fact_collection(fact_collection_json)

            # Send signal so fingerprint engine processes raw facts
            pfc_signal.send(sender=self.__class__,
                            instance=fact_collection)

            return fact_collection.id
        else:
            logger.error('No facts gathered from scan.')
            return None

    def __str__(self):
        """Convert to string."""
        return '{' + 'scan_job:{}, '.format(self.scan_job.id) + '}'
