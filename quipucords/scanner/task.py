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

from api.models import ScanTask


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
        self.results = None

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
        """Access gathered facts from ScanTask.

        Facts may need to be rebuilt from persisted results.

        :returns: Dictionary of facts
        """
        if not self.facts:
            self.facts = {}
        return self.facts

    def get_results(self):
        """Access results from ScanTask.

        Results are expected to be persisted. This method should
        understand how to read persisted results into a dictionary
        using a ScanTask object so others can retrieve them if needed.

        :returns: Dictionary of facts
        """
        if not self.results:
            self.results = {}
        return self.results

    def __str__(self):
        """Convert to string."""
        return '{' + 'scan_job:{}, '\
            'scan_task: {}, '\
            'sequence_number: {}'.format(self.scan_job.id,
                                         self.scan_task.id,
                                         self.scan_task.sequence_number) + '}'
