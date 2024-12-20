"""Test the scanner.tasks.finalize_scan function.

Note that some of these tests use pytest-celery's celery_worker fixture.
Due to issues in Celery, celery_worker fixture tests that use the database
must also set transaction=True. Using the celery_worker fixture embeds a
live worker for and executes slower than using CELERY_TASK_ALWAYS_EAGER
which bypasses several important layers of the Celery stack. Please choose
carefully whether you want the live worker or CELERY_TASK_ALWAYS_EAGER as
you update or add more tests.
"""

from unittest.mock import ANY, patch

import pytest
from django.test import override_settings

from api.models import Report, ScanJob, ScanTask
from constants import DataSources
from scanner import job, tasks
from tests.factories import ScanJobFactory, ScanTaskFactory, SourceFactory
from tests.utils import fake_semver, raw_facts_generator


@pytest.fixture
def connect_scan_job():
    """Prepare a "connect" type ScanJob."""
    connect_task = ScanTaskFactory(
        source__source_type=DataSources.OPENSHIFT,
        scan_type=ScanTask.SCAN_TYPE_CONNECT,
        status=ScanTask.PENDING,
        job__scan_type=ScanTask.SCAN_TYPE_CONNECT,
        job__status=ScanTask.PENDING,
    )
    return connect_task.job


@pytest.fixture
def inspect_scan_job():
    """Prepare an "inspect" type ScanJob.

    This ScanJob includes 3 ScanTasks: connect, inspect, and fingerprint.
    """
    scan_job = ScanJobFactory(
        scan_type=ScanTask.SCAN_TYPE_INSPECT, status=ScanTask.PENDING
    )
    source = SourceFactory()
    scan_tasks = [
        ScanTaskFactory(
            job=scan_job,
            scan_type=ScanTask.SCAN_TYPE_CONNECT,
            status=ScanTask.PENDING,
            source=source,
        ),
        ScanTaskFactory(
            job=scan_job,
            scan_type=ScanTask.SCAN_TYPE_INSPECT,
            status=ScanTask.PENDING,
            source=source,
        ),
        ScanTaskFactory(
            job=scan_job,
            scan_type=ScanTask.SCAN_TYPE_FINGERPRINT,
            status=ScanTask.PENDING,
            source=None,
        ),
    ]
    scan_job.tasks.set(scan_tasks)
    return scan_job


@pytest.fixture
def inspect_scan_job_multiple_sources():
    """Prepare an "inspect" type ScanJob with multiple Sources.

    This ScanJob includes six ScanTasks: 2 connect (one per Source), 2 inspect (one per
    source), and 1 fingerprint.
    """
    scan_job = ScanJobFactory(
        scan_type=ScanTask.SCAN_TYPE_INSPECT, status=ScanTask.PENDING
    )
    source_a, source_b = SourceFactory.create_batch(size=2)
    scan_tasks = [
        ScanTaskFactory(
            job=scan_job,
            scan_type=ScanTask.SCAN_TYPE_CONNECT,
            status=ScanTask.PENDING,
            source=source_a,
        ),
        ScanTaskFactory(
            job=scan_job,
            scan_type=ScanTask.SCAN_TYPE_CONNECT,
            status=ScanTask.PENDING,
            source=source_b,
        ),
        ScanTaskFactory(
            job=scan_job,
            scan_type=ScanTask.SCAN_TYPE_INSPECT,
            status=ScanTask.PENDING,
            source=source_a,
        ),
        ScanTaskFactory(
            job=scan_job,
            scan_type=ScanTask.SCAN_TYPE_INSPECT,
            status=ScanTask.PENDING,
            source=source_b,
        ),
        ScanTaskFactory(
            job=scan_job,
            scan_type=ScanTask.SCAN_TYPE_FINGERPRINT,
            status=ScanTask.PENDING,
            source=None,
        ),
    ]
    scan_job.tasks.set(scan_tasks)
    return scan_job


@pytest.fixture(params=(DataSources.values))
def fingerprint_only_scanjob(request, faker):
    """
    Prepare a "fingerprint" type ScanJob of all possible data sources.

    Note: tests consuming this fixture will run once for each kind of DataSource, as if
    they were decorated by pytest.mark.parametrize.
    """
    source_type = request.param
    raw_sources = [
        {
            "source_type": source_type,
            "source_name": faker.slug(),
            "server_id": faker.uuid4(),
            "report_version": f"{fake_semver()}+{faker.sha1()}",
            "facts": list(raw_facts_generator(source_type, 1)),
        }
    ]
    scan_job: ScanJob = ScanJobFactory(
        scan_type=ScanTask.SCAN_TYPE_FINGERPRINT, report=Report.objects.create()
    )
    scan_job.ingest_sources(raw_sources)
    scan_job.queue()

    return scan_job


@pytest.fixture
def mock__celery_run_task_runner():
    """Mock the body of the celery_run_task_runner Celery task.

    Mocked return values are generic placeholders so the return types are consistent.
    They may be further overridden in tests that need to specific return values.
    """
    with patch.object(tasks, "_celery_run_task_runner") as mock_task:
        mock_task.return_value = True, 1, None
        yield mock_task


@pytest.fixture
def mock__fingerprint():
    """Mock the body of the fingerprint Celery task.

    Mocked return values are generic placeholders so the return types are consistent.
    They may be further overridden in tests that need to specific return values.
    """
    with patch.object(tasks, "_fingerprint") as mock_task:
        mock_task.return_value = True, 1, None
        yield mock_task


@pytest.fixture
def mock__finalize_scan():
    """Mock the body of the finalize_scan Celery task.

    Mocked return values are generic placeholders so the return types are consistent.
    They may be further overridden in tests that need to specific return values.
    """
    with patch.object(tasks, "_finalize_scan") as mock_task:
        mock_task.return_value = True, 1, None
        yield mock_task


@pytest.mark.django_db
def test_celery_based_job_runner(connect_scan_job):
    """Test that the correct not-CeleryBasedScanJobRunner class is chosen."""
    job_runner = job.ScanJobRunner(connect_scan_job)
    assert isinstance(job_runner, job.CeleryBasedScanJobRunner)


@pytest.mark.django_db(transaction=True)
def test_run_celery_based_job_runner_only_connect(
    mock__celery_run_task_runner,
    mock__fingerprint,
    mock__finalize_scan,
    celery_worker,
    connect_scan_job,
):
    """Test the task calls for running a connect-type ScanJob."""
    job_runner = job.ScanJobRunner(connect_scan_job)
    assert isinstance(job_runner, job.CeleryBasedScanJobRunner)

    async_result = job_runner.run()
    async_result.get()

    scan_task = connect_scan_job.tasks.first()
    source_type = scan_task.source.source_type
    mock__celery_run_task_runner.assert_called_once()
    assert mock__celery_run_task_runner.call_args.kwargs == {
        "scan_task_id": scan_task.id,
        "source_type": source_type,
        "scan_type": ScanTask.SCAN_TYPE_CONNECT,
        "task_instance": ANY,
    }
    mock__fingerprint.assert_not_called()
    mock__finalize_scan.assert_called_once()


@pytest.mark.django_db(transaction=True)
def test_run_celery_based_job_runner_inspect_one_job_one_source(
    mock__celery_run_task_runner,
    mock__fingerprint,
    mock__finalize_scan,
    celery_worker,
    inspect_scan_job,
):
    """Test the task calls for running an inspect-type ScanJob."""
    job_runner = job.ScanJobRunner(inspect_scan_job)
    assert isinstance(job_runner, job.CeleryBasedScanJobRunner)

    async_result = job_runner.run()
    async_result.get()

    mock__celery_run_task_runner.assert_called()
    assert mock__celery_run_task_runner.call_count == 2  # 1 inspect and 1 connect
    mock__fingerprint.assert_called_once()
    mock__finalize_scan.assert_called_once()


@pytest.mark.django_db(transaction=True)
def test_run_celery_based_job_runner_inspect_one_job_multiple_sources(
    mock__celery_run_task_runner,
    mock__fingerprint,
    mock__finalize_scan,
    celery_worker,
    inspect_scan_job_multiple_sources,
):
    """Test the task calls for running an inspect-type ScanJob with two Sources."""
    job_runner = job.ScanJobRunner(inspect_scan_job_multiple_sources)
    assert isinstance(job_runner, job.CeleryBasedScanJobRunner)

    async_result = job_runner.run()
    async_result.get()

    mock__celery_run_task_runner.assert_called()
    assert mock__celery_run_task_runner.call_count == 4  # 2 sources * 2 tasks
    mock__fingerprint.assert_called_once()
    mock__finalize_scan.assert_called_once()


@pytest.mark.django_db
@pytest.mark.dbcompat
def test_fingerprint_job_greenpath(fingerprint_only_scanjob):
    """Test that a fingerprint-only scanjob can be run successfully."""
    assert (
        not fingerprint_only_scanjob.report.deployment_report
    ), "scanjob seems to be already completed"
    job_runner = job.ScanJobRunner(fingerprint_only_scanjob)
    assert isinstance(job_runner, job.CeleryBasedScanJobRunner)
    with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
        async_result = job_runner.run()
        async_result.get()

    fingerprint_only_scanjob.refresh_from_db()
    assert fingerprint_only_scanjob.status == ScanTask.COMPLETED
    # don't mind the lack of "s" in "report.deployment_report" - this shall be NUKED in
    #  the near future
    deployments_report = fingerprint_only_scanjob.report.deployment_report
    assert deployments_report.id
    assert deployments_report.system_fingerprints.count() == 1


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@pytest.mark.django_db
def test_fingerprint_job_canceled(fingerprint_only_scanjob, mocker):
    """Test that a fingerprint scan job handles if a scan job is canceled."""
    assert (
        not fingerprint_only_scanjob.report.deployment_report
    ), "scanjob seems to be already completed"
    job_runner = job.ScanJobRunner(fingerprint_only_scanjob)
    assert isinstance(job_runner, job.CeleryBasedScanJobRunner)
    mocker.patch.object(tasks, "scan_job_is_canceled", return_value=True)
    async_result = job_runner.run()
    async_result.get()

    fingerprint_only_scanjob.refresh_from_db()
    assert fingerprint_only_scanjob.status == ScanTask.CANCELED
