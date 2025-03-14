"""
pytest config for quipucords.

IMPORTANT: Don't import application code on toplevel as this can influence
the proper patching.
"""

from functools import partial
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core import management
from django.test import Client as DjangoClient

pytest_plugins = ("celery.contrib.pytest",)


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Force db sequences to use random numbers."""
    with django_db_blocker.unblock():
        # randomize db sequences to avoid ID coincidences causing
        # false positive tests, avoid hardcoded IDs, and attempt
        # to simulate a real world-like scenario.
        management.call_command("randomize_db_sequences")


@pytest.fixture(autouse=True)
def skip_celery_task_is_revoked(mocker):
    """
    Bypass celery_task_is_revoked when running tests.

    celery_task_is_revoked will never work in isolated unit test runs because it
    requires Celery to have a real running broker/result backend (e.g. Redis).
    """
    with mocker.patch("scanner.tasks.celery_task_is_revoked", return_value=False):
        yield


@pytest.fixture(autouse=True)
def disable_redis_cache(settings):
    """Disable the Redis backend cache and use the local memory cache instead."""
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        },
        "redis": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        },
    }


@pytest.fixture(autouse=True)
def default_data_dir(settings, tmp_path: Path) -> Path:
    """Set a clean data dir for storing files."""
    data_dir = tmp_path / "data"
    settings.DEFAULT_DATA_DIR = data_dir
    settings.LOG_DIRECTORY = data_dir / "logs"
    settings.LOG_DIRECTORY.mkdir(parents=True)
    settings.QUIPUCORDS_CACHED_REPORTS_DATA_DIR = data_dir / "cached_reports"
    settings.QUIPUCORDS_CACHED_REPORTS_DATA_DIR.mkdir(parents=True)
    return data_dir


@pytest.fixture
def qpc_user_simple(faker):
    """
    Create simpler qpc test user with no password.

    For tests that don't actually need a password, this is much faster than qpc_user.
    """
    return get_user_model().objects.create(username=faker.user_name())


class ResponseMixin:
    """Mixin intended to expand Django's Response with QoL features from requests."""

    @property
    def ok(self):
        """Returns True if response is OK."""
        return 200 <= self.status_code < 300

    @property
    def text(self):
        """Returns unicode representation of response.content."""
        return self.content.decode()


class Client(DjangoClient):
    """Django client for tests with some QoL changes."""

    def request(self, **request):
        """Patched request method for juicy DX/QoL changes."""
        response = super().request(**request)

        # we can't simply replace django's HttpResponse because
        # error responses are specialized classes, with attributes
        # like .status_code defined as class attributes.
        class CustomResponse(response.__class__, ResponseMixin):
            """Add our custom Response methods to django response."""

        response.__class__ = CustomResponse
        return response

    def post(self, *args, **kwargs):
        """POST request."""
        # set application/json as default for improved ergonomics
        kwargs.setdefault("content_type", "application/json")
        return super().post(*args, **kwargs)

    def put(self, *args, **kwargs):
        """PUT request."""
        # set application/json as default for improved ergonomics
        kwargs.setdefault("content_type", "application/json")
        return super().put(*args, **kwargs)

    def patch(self, *args, **kwargs):
        """PATCH request."""
        # set application/json as default for improved ergonomics
        kwargs.setdefault("content_type", "application/json")
        return super().patch(*args, **kwargs)


@pytest.fixture
def client_logged_in(qpc_user_simple, settings) -> Client:
    """Create a simpler Django test client with logged-in user."""
    # Why this override_settings? See:
    # https://whitenoise.readthedocs.io/en/stable/django.html#whitenoise-makes-my-tests-run-slow
    settings.WHITENOISE_AUTOREFRESH = True
    # for some reason removing DEFAULT_THROTTLING_CLASSES+RATES has no effect on
    # throttling configuration, but it can at least be raised so tests won't be rate
    # limited.
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["user"] = "9000/second"
    client = Client()
    client.force_login(user=qpc_user_simple)
    yield client


@pytest.fixture
def client_logged_out(settings) -> Client:
    """Create a simpler Django test client without a logged-in user."""
    settings.WHITENOISE_AUTOREFRESH = True
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["user"] = "9000/second"
    client = Client()
    yield client


@pytest.fixture(scope="module")
def vcr_config(_vcr_uri_map):
    """
    VCR configuration - should match the kwargs expected by VCR.use_cassettes.

    https://github.com/kiwicom/pytest-recording#configuration
    https://vcrpy.readthedocs.io/en/latest/configuration.html
    """
    replace_cassette_uri = partial(_replace_cassette_uri, uri_map=_vcr_uri_map)
    return {
        "filter_headers": [
            ("authorization", "<AUTH_TOKEN>"),
        ],
        "before_record_request": replace_cassette_uri,
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
            assert attr_value.value not in uri_map, (
                f"URI {attr_value.value} already in use."
            )
            uri_map[attr_value.value] = attr_value.fallback_value
            uri_map[attr_value.fallback_value] = attr_value.fallback_value
    return uri_map


def _replace_cassette_uri(vcr_request, uri_map: dict):
    """
    Replace recorded request URI with its equivalent fallback URI.

    Cassette recorded URIs are intended to be set on ConstantsFromEnv class
    (see tests/constants.py module).
    """
    from tests.constants import VCR_NO_PORT_URI_PORTS

    # https://vcrpy.readthedocs.io/en/latest/advanced.html#custom-request-filtering

    if vcr_request.port in VCR_NO_PORT_URI_PORTS:
        vcr_base_uri = f"{vcr_request.scheme}://{vcr_request.host}"
    else:
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
                "--refresh-cassettes option should not run with multiple processes"
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
