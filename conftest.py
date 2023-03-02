"""
pytest config for quipucords.

IMPORTANT: Don't import aplication code on toplevel as this can influence
the proper patching.
"""
# pylint: disable=import-outside-toplevel
from functools import partial
from urllib.parse import urljoin

import pytest

from tests.utils.http import BaseUrlClient


@pytest.fixture(autouse=True)
def scan_manager(mocker):
    """return a DummyScanManager instance."""
    # pylint: disable=protected-access
    from tests.dummy_scan_manager import DummyScanManager

    _manager = DummyScanManager()
    mocker.patch("scanner.manager.Manager", DummyScanManager)
    mocker.patch("scanner.manager.SCAN_MANAGER", _manager)
    yield _manager
    for job in _manager._queue:
        job.kill()
    _manager._queue = []


@pytest.fixture(scope="session")
def django_client(live_server):
    """HTTP client which connects to django live server."""
    client = BaseUrlClient(
        base_url=urljoin(live_server.url, "api/v1/"),
    )
    return client


@pytest.fixture(scope="module")
def vcr_config(_vcr_uri_map):
    """
    VCR configuration - should match the kwargs expected by VCR.use_cassettes.

    https://github.com/kiwicom/pytest-recording#configuration
    https://vcrpy.readthedocs.io/en/latest/configuration.html
    """
    replace_cassete_uri = partial(_replace_cassete_uri, uri_map=_vcr_uri_map)
    return {
        "filter_headers": [
            ("authorization", "<AUTH_TOKEN>"),
        ],
        "before_record_request": replace_cassete_uri,
    }


@pytest.fixture(scope="module")
def _vcr_uri_map():
    """Return a dict mapping testing base URIs to its fallback values."""
    from tests.constants import ConstantsFromEnv
    from tests.env import BaseURI, EnvVar

    uri_map = {}
    for attr_name in dir(ConstantsFromEnv):
        if attr_name.startswith("_"):
            continue
        attr_value = getattr(ConstantsFromEnv, attr_name)
        if isinstance(attr_value, EnvVar) and attr_value.coercer == BaseURI:
            assert (
                attr_value.value not in uri_map
            ), f"URI {attr_value.value} already in use."
            uri_map[attr_value.value] = attr_value.fallback_value
            uri_map[attr_value.fallback_value] = attr_value.fallback_value
    return uri_map


def _replace_cassete_uri(vcr_request, uri_map: dict):
    """
    Replace recorded request URI with its equivalent fallback URI.

    Cassete recorded URIs are intended to be set on ConstantsFromEnv class
    (see tests/constants.py module).
    """
    # https://vcrpy.readthedocs.io/en/latest/advanced.html#custom-request-filtering

    vcr_base_uri = f"{vcr_request.scheme}://{vcr_request.host}:{vcr_request.port}"
    fallback_base_uri = uri_map[vcr_base_uri]
    vcr_request.uri = fallback_base_uri.replace_base_uri(vcr_request.uri)
    return vcr_request


def pytest_addoption(parser):
    """Add custom args to pytest cmdline."""
    parser.addoption(
        "--refresh-cassettes",
        action="store_true",
        default=False,
        help="Refresh VCR cassettes.",
    )


def pytest_configure(config):
    """Customize pytest configuration."""
    from _pytest.config.exceptions import UsageError

    record_mode_is_none = config.option.record_mode in [None, "none"]
    if config.option.refresh_cassettes:
        if record_mode_is_none:
            config.option.record_mode = "new_episodes"
        # only execute tests marked with vcr_primer
        config.option.markexpr = "vcr_primer"
        num_processes = config.option.numprocesses or 1
        if num_processes > 1:
            raise UsageError(
                "--refresh-cassetes option should not run with multiple processes"
                " UNLESS the implementation of OCP api tests that depend on"
                " dynamic client are adapted."
            )
    elif not record_mode_is_none:
        raise UsageError(
            "Quipucords VCR cassettes should be recorded with --refresh-cassettes"
            " option explicitly set."
        )
    # document quipucords custom markers
    markers = [
        "dbcompat: marks tests using our db compat module.",
        "integration: marks tests as integration tests"
        " (deselect with '-m \"not integration\"')",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')",
        "vcr_primer: tests intended to record vcr cassettes.",
    ]
    for mark in markers:
        config.addinivalue_line("markers", mark)


def pytest_collection_modifyitems(config, items):
    """Modify tests as they are collected."""
    for item in items:
        # vcr_primer marker config
        if "vcr_primer" in item.keywords:
            # inject vcr markers - allows vcr_primer marked tests to not require
            # these markers (which might look redundant for readers)
            vcr_primer = list(item.iter_markers(name="vcr_primer"))[0]
            if "vcr" not in item.keywords:
                if not config.option.refresh_cassettes and len(vcr_primer.args) > 1:
                    # pytest-recording combines all extra cassettes in one single blob
                    # https://github.com/kiwicom/pytest-recording/blob/2643539b634b746cb2e989e0e6a17e157a1bde3a/src/pytest_recording/_vcr.py#L84-L86
                    # this is fine for us when --record-mode set to "none", but in
                    # any other scenario this would lead to data duplication and
                    # nullyfing the advantage of using multiple cassettes at the
                    # same time
                    item.add_marker(pytest.mark.vcr(*vcr_primer.args[1:]))
                else:
                    item.add_marker(pytest.mark.vcr)
            if "default_cassette" not in item.keywords:
                item.add_marker(pytest.mark.default_cassette(vcr_primer.args[0]))
