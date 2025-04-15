"""Test ScanJobSerializerV1 and related v1 serializer functions."""

import pytest

from api.models import Scan, ScanJob, ScanTask
from api.scanjob.serializer_v1 import ScanJobSerializerV1, expand_scanjob
from tests.api.scan.test_scan import (
    disabled_optional_products_default,
    enabled_extended_product_search_default,
)
from tests.factories import SourceFactory
from tests.scanner.test_util import (
    create_scan_job,
    create_scan_job_two_tasks,
    scan_options_products,
)

pytestmark = pytest.mark.django_db  # all user tests require the database


def test_get_extra_vars():
    """Tests the get_extra_vars method with empty dict."""
    scan_options = {
        "disabled_optional_products": disabled_optional_products_default(),
        "enabled_extended_product_search": (enabled_extended_product_search_default()),
    }
    scan_job, _ = create_scan_job(SourceFactory(), scan_options=scan_options)
    extra_vars = scan_job.get_extra_vars()

    expected_vars = {
        "jboss_eap": True,
        "jboss_fuse": True,
        "jboss_ws": True,
        "jboss_eap_ext": False,
        "jboss_fuse_ext": False,
        "jboss_ws_ext": False,
    }
    assert extra_vars == expected_vars

    json_disabled, json_enabled_ext = scan_options_products(expected_vars)

    serializer = ScanJobSerializerV1(scan_job)
    json_scan = serializer.data
    assert json_scan.get("options").get("disabled_optional_products") == json_disabled
    assert (
        json_scan.get("options").get("enabled_extended_product_search")
        == json_enabled_ext
    )


def test_get_extra_vars_missing_disable_product():
    """Tests the get_extra_vars with extended search None."""
    scan_options = {"disabled_optional_products": disabled_optional_products_default()}
    scan_job, _ = create_scan_job(SourceFactory(), scan_options=scan_options)
    extra_vars = scan_job.get_extra_vars()

    expected_vars = {
        "jboss_eap": True,
        "jboss_fuse": True,
        "jboss_ws": True,
        "jboss_eap_ext": False,
        "jboss_fuse_ext": False,
        "jboss_ws_ext": False,
    }
    assert extra_vars == expected_vars

    json_disabled, _ = scan_options_products(expected_vars)

    serializer = ScanJobSerializerV1(scan_job)
    json_scan = serializer.data
    assert json_scan.get("options").get("disabled_optional_products") == json_disabled
    assert json_scan.get("options").get("enabled_extended_product_search") is None


def test_get_extra_vars_missing_extended_search():
    """Tests the get_extra_vars with disabled products None."""
    scan_options = {
        "enabled_extended_product_search": (enabled_extended_product_search_default()),
    }
    scan_job, _ = create_scan_job(SourceFactory(), scan_options=scan_options)
    extra_vars = scan_job.get_extra_vars()

    expected_vars = {
        "jboss_eap": True,
        "jboss_fuse": True,
        "jboss_ws": True,
        "jboss_eap_ext": False,
        "jboss_fuse_ext": False,
        "jboss_ws_ext": False,
    }
    assert extra_vars == expected_vars

    _, json_enabled_ext = scan_options_products(expected_vars)

    serializer = ScanJobSerializerV1(scan_job)
    json_scan = serializer.data
    assert json_scan.get("options").get("disabled_optional_products") is None
    assert (
        json_scan.get("options").get("enabled_extended_product_search")
        == json_enabled_ext
    )


def test_get_extra_vars_extended_search():
    """Tests the get_extra_vars method with extended search."""
    extended = {
        "jboss_eap": True,
        "jboss_fuse": True,
        "jboss_ws": True,
        Scan.EXT_PRODUCT_SEARCH_DIRS: ["a", "b"],
    }
    scan_options = {
        "disabled_optional_products": disabled_optional_products_default(),
        "enabled_extended_product_search": extended,
    }
    scan_job, _ = create_scan_job(SourceFactory(), scan_options=scan_options)
    extra_vars = scan_job.get_extra_vars()

    expected_vars = {
        "jboss_eap": True,
        "jboss_fuse": True,
        "jboss_ws": True,
        "jboss_eap_ext": True,
        "jboss_fuse_ext": True,
        "jboss_ws_ext": True,
        "search_directories": "a b",
    }
    assert extra_vars == expected_vars

    json_disabled, json_enabled_ext = scan_options_products(expected_vars)

    serializer = ScanJobSerializerV1(scan_job)
    json_scan = serializer.data
    assert json_scan.get("options").get("disabled_optional_products") == json_disabled
    assert json_scan.get("options").get(
        "enabled_extended_product_search"
    ) == json_enabled_ext | {"search_directories": ["a", "b"]}


def test_get_extra_vars_mixed():
    """Tests the get_extra_vars method with mixed values."""
    disabled = {
        "jboss_eap": True,
        "jboss_fuse": True,
        "jboss_ws": False,
    }
    scan_options = {
        "disabled_optional_products": disabled,
        "enabled_extended_product_search": (enabled_extended_product_search_default()),
    }
    scan_job, _ = create_scan_job(SourceFactory(), scan_options=scan_options)
    extra_vars = scan_job.get_extra_vars()

    expected_vars = {
        "jboss_eap": True,
        "jboss_fuse": False,
        "jboss_ws": True,
        "jboss_eap_ext": False,
        "jboss_fuse_ext": False,
        "jboss_ws_ext": False,
    }
    assert extra_vars == expected_vars

    json_disabled, json_enabled_ext = scan_options_products(expected_vars)

    serializer = ScanJobSerializerV1(scan_job)
    json_scan = serializer.data
    # jboss_eap is calculated based on all the other values - it's easier this way
    assert json_scan.get("options").get(
        "disabled_optional_products"
    ) == json_disabled | {"jboss_eap": True}
    assert (
        json_scan.get("options").get("enabled_extended_product_search")
        == json_enabled_ext
    )


def test_get_extra_vars_false():
    """Tests the get_extra_vars method with all False."""
    extended = enabled_extended_product_search_default()
    disabled = {
        "jboss_eap": True,
        "jboss_fuse": True,
        "jboss_ws": True,
    }
    scan_options = {
        "disabled_optional_products": disabled,
        "enabled_extended_product_search": extended,
    }
    scan_job, _ = create_scan_job(SourceFactory(), scan_options=scan_options)

    extra_vars = scan_job.get_extra_vars()

    expected_vars = {
        "jboss_eap": False,
        "jboss_fuse": False,
        "jboss_ws": False,
        "jboss_eap_ext": False,
        "jboss_fuse_ext": False,
        "jboss_ws_ext": False,
    }
    assert extra_vars == expected_vars

    json_disabled, json_enabled_ext = scan_options_products(expected_vars)

    serializer = ScanJobSerializerV1(scan_job)
    json_scan = serializer.data
    assert json_scan.get("options").get("disabled_optional_products") == json_disabled
    assert (
        json_scan.get("options").get("enabled_extended_product_search")
        == json_enabled_ext
    )


def test_expand_scanjob():
    """Test view expand_scanjob."""
    scan_job, scan_task = create_scan_job(SourceFactory())
    scan_job.status = ScanTask.RUNNING
    scan_job.save()
    scan_task.update_stats(
        "TEST_VC.", sys_count=2, sys_failed=1, sys_scanned=1, sys_unreachable=0
    )

    scan_job = ScanJob.objects.filter(pk=scan_job.id).first()
    serializer = ScanJobSerializerV1(scan_job)
    json_scan = serializer.data
    json_scan = expand_scanjob(json_scan)

    assert json_scan.get("systems_count") == 2
    assert json_scan.get("systems_failed") == 1
    assert json_scan.get("systems_scanned") == 1


def test_expand_scanjob_calc():
    """Test view expand_scanjob calculations."""
    scan_job, scan_tasks = create_scan_job_two_tasks(SourceFactory(), SourceFactory())
    scan_job.status = ScanTask.RUNNING
    scan_job.save()
    counts = (
        (10, 9, 1, 0),  # inspect source 1
        (39, 30, 2, 7),  # inspect source 2
    )
    for task, count_spec in zip(scan_tasks, counts):
        count, scanned, failed, unreachable = count_spec
        task.update_stats(
            f"test-{count}",
            sys_count=count,
            sys_scanned=scanned,
            sys_failed=failed,
            sys_unreachable=unreachable,
        )

    scan_job = ScanJob.objects.filter(pk=scan_job.id).first()
    serializer = ScanJobSerializerV1(scan_job)
    json_scan = serializer.data
    json_scan = expand_scanjob(json_scan)

    assert json_scan.get("systems_count") == 49
    assert json_scan.get("systems_scanned") == 39
    assert json_scan.get("systems_failed") == 3
    assert json_scan.get("systems_unreachable") == 7

    for json_task, count_spec in zip(json_scan.get("tasks"), counts):
        count, scanned, failed, unreachable = count_spec
        assert json_task.get("systems_count") == count
        assert json_task.get("systems_scanned") == scanned
        assert json_task.get("systems_failed") == failed
        assert json_task.get("systems_unreachable") == unreachable
