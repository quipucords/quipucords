"""Test util for the scan features."""

from api.models import Scan, ScanJob, ScanTask


def create_scan_job(
    source, scan_type=ScanTask.SCAN_TYPE_CONNECT, scan_name="test", scan_options=None
):
    """Create a new scan job.

    :param source: the source for the scan job
    :param scan_type: Either connect or inspect
    :param scan_options: Job scan options
    :return: the scan job and task
    """
    # Create scan configuration
    scan = Scan.objects.create(name=scan_name, scan_type=scan_type)

    # Add source to scan
    if source is not None:
        scan.sources.add(source)

    # Add options to scan
    if scan_options is not None:
        scan.options = scan_options
        scan.save()

    # Create Job
    scan_job = ScanJob.objects.create(scan=scan)

    scan_job.queue()

    # pylint: disable=no-member
    scan_task = scan_job.tasks.first()
    if scan_type == ScanTask.SCAN_TYPE_INSPECT:
        scan_task.status_complete()
        scan_task = scan_job.tasks.filter(scan_type=ScanTask.SCAN_TYPE_INSPECT).first()

    return scan_job, scan_task


def create_scan_job_two_tasks(
    source,
    source2,
    scan_type=ScanTask.SCAN_TYPE_CONNECT,
    scan_name="test",
    scan_options=None,
):
    """Create a new scan job with two sources.

    :param source: the source for the scan job
    :param sourc2: the second source for the scan job
    :param scan_type: Either connect or inspect
    :param scan_options: Job scan options
    :return: the scan job and task
    """
    # Create scan configuration
    scan = Scan.objects.create(name=scan_name, scan_type=scan_type)

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
    scan_job = ScanJob.objects.create(scan=scan)

    scan_job.queue()

    # grab the scan tasks
    scan_tasks = scan_job.tasks.all().order_by("sequence_number")
    if scan_type == ScanTask.SCAN_TYPE_INSPECT:
        for task in scan_tasks:
            task.status_complete()

    return scan_job, scan_tasks
