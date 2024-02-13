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


def scan_options_products(expected_vars_dict):
    """Turn expected_extra_vars into options JSON.

    This is roughly reverse operation for
    ScanOptions.get_extra_vars(), except it doesn't handle all the complexity
    of jboss_eap disabled option for simplicity

    :param expected_vars_dict: return value of ScanOptions.get_extra_vars()
    :return: 2-tuple of dicts that can be compared to serializer.data
    """
    disabled_optional_products = {
        key: not expected_vars_dict[key]
        for key in ("jboss_eap", "jboss_fuse", "jboss_brms", "jboss_ws")
    }

    enabled_extended_product_search = {
        key: expected_vars_dict[f"{key}_ext"]
        for key in ("jboss_eap", "jboss_fuse", "jboss_brms", "jboss_ws")
    }

    return (disabled_optional_products, enabled_extended_product_search)
