# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

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
