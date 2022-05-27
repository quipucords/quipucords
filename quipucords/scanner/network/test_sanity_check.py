# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Static checks for network ymls."""

import pytest

from scanner.network.utils import _yaml_load


@pytest.fixture
def path_to_playbooks(settings):
    """Path to network scan playbooks."""
    return settings.BASE_DIR / "scanner/network/runner"


def test_connect_yml(path_to_playbooks):
    """Check if connect.yml a valid yaml."""
    path = path_to_playbooks / "connect.yml"
    connect_data = _yaml_load(path)
    assert connect_data


@pytest.fixture
def inspect_yml_path(path_to_playbooks):
    """Path to inspect.yml playbook."""
    return path_to_playbooks / "inspect.yml"


def test_check_host_done(inspect_yml_path):
    """Sanity check inspect.yml content."""
    inspect_data = _yaml_load(inspect_yml_path)
    assert isinstance(inspect_data, list)
    assert len(inspect_data) == 1
    assert isinstance(inspect_data[0], dict)
    assert (
        inspect_data[0]["roles"][-1] == "host_done"
    ), "host_done SHOULD be the last role"


def test_check_all_roles_are_included(inspect_yml_path, path_to_playbooks):
    """
    Sanity check for implemented roles.

    If a role is implemented but not used this will raise an error.
    """
    role_names = {
        playbook.parent.parent.name
        for playbook in path_to_playbooks.rglob("roles/*/tasks/main.yml")
    }
    inspect_data = _yaml_load(inspect_yml_path)
    assert role_names == set(inspect_data[0]["roles"])
