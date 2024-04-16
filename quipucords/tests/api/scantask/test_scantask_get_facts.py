"""Test ScanTask.get_facts."""

from functools import partial

import pytest

from api.models import ScanTask
from tests.factories import ScanTaskFactory


@pytest.fixture
def raw_facts_list(faker):
    """Fixture representing a list of random facts."""
    # name "fact" will be use to order "systems" in test_content
    return [
        {
            "name": faker.slug(),
            faker.slug(): faker.pybool(),
            faker.slug(): faker.pyint(max_value=100),
        }
        for _ in range(10)
    ]


@pytest.fixture
def inspection_scantask(raw_facts_list):
    """ScanTask instance mapped to raw_facts_list."""
    return ScanTaskFactory(
        scan_type=ScanTask.SCAN_TYPE_INSPECT,
        with_raw_facts=raw_facts_list,
    )


@pytest.mark.django_db
def test_content(raw_facts_list, inspection_scantask: ScanTask):
    """Check if get_facts content is equal to the original data."""
    # ensure facts are on the same order to avoid failures (ordering might
    # vary, and that's fine - this test only cares about the content)
    fact_sorter = partial(sorted, key=lambda d: d["name"])
    assert fact_sorter(raw_facts_list) == fact_sorter(inspection_scantask.get_facts())


@pytest.mark.django_db
def test_number_of_queries(
    django_assert_max_num_queries,
    inspection_scantask: ScanTask,
):
    """Ensure get_facts doesn't span lots of queries."""
    with django_assert_max_num_queries(2):
        inspection_scantask.get_facts()
