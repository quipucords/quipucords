"""Test the API application."""

from typing import TYPE_CHECKING

import pytest

from api.models import (
    InspectGroup,
    InspectResult,
    ScanJob,
    ScanTask,
)
from tests.api.scan.test_scan import (
    disabled_optional_products_default,
    enabled_extended_product_search_default,
)
from tests.factories import (
    InspectResultFactory,
    ReportFactory,
    ScanFactory,
    ScanJobFactory,
    ScanTaskFactory,
    SourceFactory,
)
from tests.scanner.test_util import (
    create_scan_job,
)

if TYPE_CHECKING:
    from api.models import Report, ScanJob


pytestmark = pytest.mark.django_db  # all tests here require the database


def test_queue_task():
    """Test create queue state change."""
    scan_options = {
        "disabled_optional_products": disabled_optional_products_default(),
        "enabled_extended_product_search": (enabled_extended_product_search_default()),
    }
    scan = ScanFactory(options=scan_options)
    scanjob = ScanJobFactory(scan=scan)
    # scanjob = ScanJob.objects.create(scan=scan)

    # Job in created state
    assert scanjob.status == ScanTask.CREATED
    tasks = scanjob.tasks.all()
    assert len(tasks) == 0

    # Queue job to run
    scanjob.queue()

    # Job should be in pending state
    assert scanjob.status == ScanTask.PENDING

    # Queue should have created scan tasks
    tasks = scanjob.tasks.all().order_by("sequence_number")
    assert len(tasks) == 2

    # Validate inspect task created and correct
    inspect_task = tasks[0]
    assert inspect_task.scan_type == ScanTask.SCAN_TYPE_INSPECT
    assert inspect_task.status == ScanTask.PENDING

    # Validate fingerprint task created and correct
    inspect_task = tasks[1]
    assert inspect_task.scan_type == ScanTask.SCAN_TYPE_FINGERPRINT
    assert inspect_task.status == ScanTask.PENDING


def test_queue_invalid_state_changes():
    """Test create queue failed."""
    scanjob, _ = create_scan_job(SourceFactory(), scan_type=ScanTask.SCAN_TYPE_INSPECT)
    scanjob.status = ScanTask.FAILED

    # Queue job to run
    scanjob.queue()
    assert scanjob.status == ScanTask.FAILED

    assert not scanjob.status_complete()
    assert scanjob.status == ScanTask.FAILED

    assert not scanjob.status_pause()
    assert scanjob.status == ScanTask.FAILED

    assert not scanjob.status_start()
    assert scanjob.status == ScanTask.FAILED

    assert not scanjob.status_cancel()
    assert scanjob.status == ScanTask.FAILED

    assert not scanjob.status_restart()
    assert scanjob.status == ScanTask.FAILED

    assert scanjob.status_fail("test failure")
    assert scanjob.status == ScanTask.FAILED

    scanjob.status = ScanTask.CREATED
    assert not scanjob.status_fail("test failure")
    assert scanjob.status == ScanTask.CREATED

    scanjob.status = ScanTask.RUNNING
    assert scanjob.status_complete()
    assert scanjob.status == ScanTask.COMPLETED


def test_start_task():
    """Test start pending task."""
    scanjob, _ = create_scan_job(SourceFactory(), scan_type=ScanTask.SCAN_TYPE_INSPECT)

    # Queue job to run
    scanjob.queue()
    assert scanjob.status == ScanTask.PENDING

    # Queue should have created inspect and fingerprint tasks
    tasks = scanjob.tasks.all()
    assert len(tasks) == 2

    # Start job
    assert scanjob.status_start()


def test_pause_restart_task():
    """Test pause and restart task."""
    scanjob, _ = create_scan_job(SourceFactory(), scan_type=ScanTask.SCAN_TYPE_INSPECT)

    # Queue job to run
    scanjob.queue()
    assert scanjob.status == ScanTask.PENDING

    # Queue should have created inspect and fingerprint tasks
    tasks = scanjob.tasks.all()
    assert len(tasks) == 2
    inspect_task = scanjob.tasks.first()
    assert inspect_task.status == ScanTask.PENDING

    # Start job
    assert scanjob.status_start()
    assert scanjob.status == ScanTask.RUNNING

    assert scanjob.status_pause()
    inspect_task = scanjob.tasks.first()
    assert scanjob.status == ScanTask.PAUSED
    assert inspect_task.status == ScanTask.PAUSED

    assert scanjob.status_restart()
    inspect_task = scanjob.tasks.first()
    assert scanjob.status == ScanTask.PENDING
    assert inspect_task.status == ScanTask.PENDING

    assert scanjob.status_cancel()
    inspect_task = scanjob.tasks.first()
    assert scanjob.status == ScanTask.CANCELED
    assert inspect_task.status == ScanTask.CANCELED


@pytest.fixture
def scanjob_with_inspect_results():
    """ScanJob with 3 InspectResults."""
    inspection_results = InspectResultFactory.create_batch(3)
    inspect_groups = InspectGroup.objects.filter(inspect_results__in=inspection_results)
    scanjob = ScanJobFactory(report=None)
    task = ScanTaskFactory(job=scanjob)
    task.inspect_groups.set(inspect_groups)
    return scanjob


@pytest.mark.django_db
def test_delete_inspect_results(scanjob_with_inspect_results: ScanJob):
    """Test ScanJob.delete_inspect_results method."""
    scanjob = scanjob_with_inspect_results
    assert InspectResult.objects.filter(inspect_group__tasks__job=scanjob).exists()
    scanjob.delete_inspect_results()
    assert not InspectResult.objects.filter(inspect_group__tasks__job=scanjob).exists()


@pytest.mark.django_db
def test_delete_inspect_results_bound_to_other_reports(
    scanjob_with_inspect_results: ScanJob,
):
    """Ensure only InspectResults uniquely bound to a ScanJob are deleted."""
    inspect_res = InspectResult.objects.first()
    other_report: Report = ReportFactory()
    inspect_res.inspect_group.reports.add(other_report)
    # save id in a variable so we can check later for existence
    inspect_res_id = inspect_res.id

    scanjob = scanjob_with_inspect_results
    assert InspectResult.objects.filter(inspect_group__tasks__job=scanjob).count() == 3
    scanjob.delete_inspect_results()
    assert InspectResult.objects.filter(inspect_group__tasks__job=scanjob).count() == 1
    assert InspectResult.objects.filter(id=inspect_res_id).exists()
    # deleting the other report should make the results deletable
    other_report.delete()
    scanjob.delete_inspect_results()
    assert InspectResult.objects.filter(inspect_group__tasks__job=scanjob).count() == 0
    assert not InspectResult.objects.filter(id=inspect_res_id).exists()


@pytest.mark.django_db
def test_scanjob_model_str():
    """Test the __str__ method."""
    scanjob = ScanJobFactory()
    scanjob_str = f"{scanjob}"
    assert f"id={scanjob.id}" in scanjob_str
    assert f"scan_type={scanjob.scan_type}" in scanjob_str
    assert f"status={scanjob.status}" in scanjob_str
