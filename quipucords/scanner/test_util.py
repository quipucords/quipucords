#
# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test util for the scan features."""

from api.models import (Scan,
                        ScanJob,
                        ScanTask)


def create_scan_job(source,
                    scan_type=ScanTask.SCAN_TYPE_CONNECT,
                    scan_name='test',
                    scan_options=None):
    """Create a new scan job.

    :param source: the source for the scan job
    :param scan_type: Either connect or inspect
    :param scan_options: Job scan options
    :return: the scan job and task
    """
    # Create scan configuration
    scan = Scan(name=scan_name,
                scan_type=scan_type)
    scan.save()

    # Add source to scan
    if source is not None:
        scan.sources.add(source)

    # Add options to scan
    if scan_options is not None:
        scan.options = scan_options
        scan.save()

    # Create Job
    scan_job = ScanJob(scan=scan)
    scan_job.save()

    scan_job.queue()

    scan_task = scan_job.tasks.first()
    if scan_type == ScanTask.SCAN_TYPE_INSPECT:
        scan_task.complete()
        scan_task = scan_job.tasks.last()

    return scan_job, scan_task


def create_scan_job_two_tasks(source,
                              source2,
                              scan_type=ScanTask.SCAN_TYPE_CONNECT,
                              scan_name='test',
                              scan_options=None):
    """Create a new scan job with two sources.

    :param source: the source for the scan job
    :param sourc2: the second source for the scan job
    :param scan_type: Either connect or inspect
    :param scan_options: Job scan options
    :return: the scan job and task
    """
    # Create scan configuration
    scan = Scan(name=scan_name,
                scan_type=scan_type)
    scan.save()

    # Add source to scan
    if source is not None:
        scan.sources.add(source)
    if source2 is not None:
        scan.sources.add(source2)

    # Add options to scan
    if scan_options is not None:
        scan.options = scan_options
        scan.save()

    # Create Job
    scan_job = ScanJob(scan=scan)
    scan_job.save()

    scan_job.queue()

    # grab the scan tasks
    scan_tasks = scan_job.tasks.all().order_by('sequence_number')
    if scan_type == ScanTask.SCAN_TYPE_INSPECT:
        for task in scan_tasks:
            task.complete()

    return scan_job, scan_tasks
