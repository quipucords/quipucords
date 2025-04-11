"""Test ScanJob custom queryset."""

import pytest

from api.models import ScanJob, ScanTask
from tests.factories import ScanJobFactory, ScanTaskFactory


@pytest.fixture
def inspect_type_scanjob():
    """Return a fixture representing a inspect type ScanJob."""
    scanjob: ScanJob = ScanJobFactory(
        scan_type=ScanTask.SCAN_TYPE_INSPECT, status=ScanTask.COMPLETED
    )
    _add_scantasks(scanjob)
    return scanjob


@pytest.fixture
def fingerprint_type_scanjob():
    """Return a fixture representing a fingerprint type ScanJob."""
    scanjob: ScanJob = ScanJobFactory(
        scan_type=ScanTask.SCAN_TYPE_FINGERPRINT, status=ScanTask.COMPLETED
    )
    _add_scantasks(scanjob)
    return scanjob


def _add_scantasks(scanjob):
    ScanTaskFactory(
        job=scanjob,
        scan_type=ScanTask.SCAN_TYPE_INSPECT,
        systems_count=20,
        systems_scanned=10,
        systems_failed=9,
        systems_unreachable=1,
    )
    # fingerprint type counts are irrelevant and should be ignored (in production they
    # are always zero). Using bigger numbers here to ensure they are ignored in
    # subsequent tests with inspection/connection jobs
    ScanTaskFactory(
        job=scanjob,
        scan_type=ScanTask.SCAN_TYPE_FINGERPRINT,
        systems_count=999,
        systems_scanned=999,
        systems_failed=999,
        systems_unreachable=999,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "scanjob,count,scanned,failed,unreachable",
    (
        ("inspect_type_scanjob", 20, 10, 9, 1),
        ("fingerprint_type_scanjob", 999, 999, 999, 999),
    ),
)
def test_with_counts(  # noqa: PLR0913
    request, scanjob, count, scanned, failed, unreachable
):
    """Test qs.with_counts results against hardcoded values in fixtures."""
    scanjob = request.getfixturevalue(scanjob)
    scanjob_with_counts = ScanJob.objects.with_counts().get(id=scanjob.id)
    assert scanjob_with_counts.systems_count == count
    assert scanjob_with_counts.systems_scanned == scanned
    assert scanjob_with_counts.systems_failed == failed
    assert scanjob_with_counts.systems_unreachable == unreachable


@pytest.mark.django_db
def test_with_counts_equivalency(inspect_type_scanjob):
    """Ensure qs.with_counts is equivalent to ScanJob.calculate_counts()."""
    scanjob = inspect_type_scanjob
    count, scanned, failed, unreachable, _ = scanjob.calculate_counts()
    scanjob_with_counts = ScanJob.objects.with_counts().get(id=scanjob.id)
    assert scanjob_with_counts.systems_count == count
    assert scanjob_with_counts.systems_scanned == scanned
    assert scanjob_with_counts.systems_failed == failed
    assert scanjob_with_counts.systems_unreachable == unreachable
