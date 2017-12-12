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

    def __init__(self, scanjob, scantask, prerequisite_tasks=None):
        """Set context for task execution.

        :param scanjob: the scan job that contains this task
        :param scantask: the scan task model for this task
        :param prerequisite_tasks: An array of scan task model objects
        that were execute prior to running this task.
        """
        self.scanjob = scanjob
        self.scantask = scantask
        self.prerequisite_tasks = prerequisite_tasks

    def run(self):
        """Block that will be executed.

        Results are expected to be persisted.  The state of
        self.scantask should be updated with status COMPLETE/FAILED
        before returning.

        :returns: Returns the status.  Must be one of the
        ScanTask.STATUS_CHOICES values
        """
        print('Running task: %s' % self.scantask)
        return ScanTask.COMPLETED

    def facts(self):
        """Provide the resulting facts for the scan task.

        :returns: Returns a dictionary of gathered facts.
        """
        return {}
