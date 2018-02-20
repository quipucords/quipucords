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

from datetime import datetime
from api.models import (Scan,
                        ScanOptions,
                        ScanTask,
                        ScanJob,
                        JobConnectionResult,
                        JobInspectionResult,
                        TaskConnectionResult,
                        TaskInspectionResult)


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
    options_to_use = scan_options
    if options_to_use is None:
        options_to_use = ScanOptions()
        options_to_use.save()

    scan.options = options_to_use
    scan.save()

    # Create job results
    job_conn_results = JobConnectionResult()
    job_conn_results.save()

    # Create task results
    task_conn_result = TaskConnectionResult()
    task_conn_result.save()

    # Create Job
    scan_job = ScanJob(scan=scan,
                       connection_results=job_conn_results)
    scan_job.save()

    # Simulate what happens via the API to copy scan config
    scan_job.copy_scan_configuration()

    # Add Task results to job results
    scan_job.connection_results.task_results.add(task_conn_result)

    # Create Connection Task
    conn_task = ScanTask(scan_type=ScanTask.SCAN_TYPE_CONNECT,
                         source=source, sequence_number=1,
                         start_time=datetime.utcnow(),
                         connection_result=task_conn_result)
    conn_task.save()

    # Add Tasks to job
    scan_job.tasks.add(conn_task)

    # Default return value
    scan_task = conn_task
    if scan_type == ScanTask.SCAN_TYPE_INSPECT:
        # Create job results
        job_inspect_results = JobInspectionResult()
        job_inspect_results.save()

        # Create task results
        task_inspect_result = TaskInspectionResult()
        task_inspect_result.save()

        # Create Job
        scan_job.inspection_results = job_inspect_results

        # Add Task results to job results
        scan_job.inspection_results.task_results.add(task_inspect_result)

        # Create Inspection Task
        scan_task = ScanTask(scan_type=ScanTask.SCAN_TYPE_INSPECT,
                             source=source, sequence_number=2,
                             start_time=datetime.utcnow(),
                             inspection_result=task_inspect_result)
        scan_task.save()

        scan_task.prerequisites.add(conn_task)
        scan_task.save()

        # Add Tasks to job
        scan_job.tasks.add(scan_task)

    scan_job.save()
    return scan_job, scan_task
