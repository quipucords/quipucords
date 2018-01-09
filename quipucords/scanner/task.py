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
"""ScanTaskRunner is a logical breakdown of work."""

from api.models import ScanTask, ConnectionResult, InspectionResult


class ScanTaskRunner(object):
    """ScanTaskRunner is a logical breakdown of work."""

    def __init__(self, scan_job, scan_task):
        """Set context for task execution.

        :param scan_job: the scan job that contains this task
        :param scan_task: the scan task model for this task
        :param prerequisite_tasks: An array of scan task model objects
        that were execute prior to running this task.
        """
        self.scan_job = scan_job
        self.scan_task = scan_task
        self.facts = None
        self.result = None

    def run(self):
        """Block that will be executed.

        Results are expected to be persisted.  The state of
        self.scan_task should be updated with status COMPLETE/FAILED
        before returning.

        :returns: Returns the status.  Must be one of the
        ScanTask.STATUS_CHOICES values
        """
        # pylint: disable=no-self-use
        return ScanTask.COMPLETED

    def get_facts(self):
        """Access inspection facts."""
        # pylint: disable=too-many-nested-blocks
        if not self.facts:
            self.facts = []
            if self.scan_task.scan_type == ScanTask.SCAN_TYPE_INSPECT:
                temp_facts = []
                system_results = self.get_result()
                if system_results:
                    # Process all results that were save to db
                    for system_result in system_results.systems.all():
                        fact = {}
                        for raw_fact in system_result.facts.all():
                            if raw_fact.value is None or raw_fact.value == '':
                                continue
                            fact[raw_fact.name] = raw_fact.value
                        temp_facts.append(fact)

                self.facts = temp_facts
        return self.facts

    def get_result(self):
        """Access results from ScanTask.

        Results are expected to be persisted. This method should
        understand how to read persisted results into a dictionary
        using a ScanTask object so others can retrieve them if needed.

        :returns: Scan result object for task (either ConnectionResult
        or InspectionResult)
        """
        if not self.result:
            if self.scan_task.scan_type == ScanTask.SCAN_TYPE_INSPECT:
                self.result = InspectionResult.objects.filter(
                    scan_task=self.scan_task.id).first()
            elif self.scan_task.scan_type == ScanTask.SCAN_TYPE_CONNECT:
                self.result = ConnectionResult.objects.filter(
                    scan_task=self.scan_task.id).first()
        return self.result

    def __str__(self):
        """Convert to string."""
        return '{' + 'scan_job:{}, '\
            'sequence_number: {}, '\
            'scan_task: {}'.format(self.scan_job.id,
                                   self.scan_task.sequence_number,
                                   self.scan_task) + '}'
