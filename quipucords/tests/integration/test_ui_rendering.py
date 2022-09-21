# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Smoke test to ensure UI is served."""

from urllib.parse import urljoin

import pytest
from bs4 import BeautifulSoup


def _parse_html(raw_html_string) -> BeautifulSoup:
    return BeautifulSoup(raw_html_string, "html.parser")


@pytest.mark.slow
@pytest.mark.integration
class TestUIRendering:
    """Smoke test UI rendering."""

    def test_home_redirect(self, qpc_client):
        """Check if an unauthenticated user will be redirected to login page."""
        response = qpc_client.get("/")
        assert response.ok, response.content
        assert len(response.history)
        assert any(resp.status_code in [301, 302] for resp in response.history)
        assert response.url == urljoin(qpc_client.base_url, "login/")

    def test_django_templates(self, qpc_client):
        """Sanity checks for django templates and styling."""
        response = qpc_client.get("/")
        assert response.ok, response.content
        parsed_html = _parse_html(response.text)
        assert parsed_html.title.string.strip() == "Quipucords"
        link_list = [link["href"] for link in parsed_html.head.find_all("link")]
        responses = [qpc_client.get(link) for link in link_list]
        assert all(response.ok for response in responses), [
            r.status_code for r in responses
        ]

    def test_client(self, qpc_client):
        """Check if spa part of the application is loaded properly."""
        response = qpc_client.get("/client")
        assert response.ok, response.content
        parsed_html = _parse_html(response.text)
        js_scripts = parsed_html.find_all("script")
        assert len(js_scripts) > 1
        # On quipucords-ui>=0.10, first script is a injected script without src path
        assert "src" not in js_scripts[0].attrs.keys()
        script_souces = [script["src"] for script in js_scripts[1:]]
        responses = [qpc_client.get(source) for source in script_souces]
        assert all(r.ok for r in responses), [r.status_code for r in responses]
