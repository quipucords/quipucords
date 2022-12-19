# Copyright (c) 2022 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test OCPEntities methods."""

from copy import deepcopy

import pytest

from scanner.openshift.entities import (
    OCPBaseEntity,
    OCPDeployment,
    OCPError,
    OCPProject,
    load_entity,
)


@pytest.mark.parametrize("reason", ["FOO", "BAR"])
@pytest.mark.parametrize("status", [999, 123, 456])
@pytest.mark.parametrize(
    "error_body,expected_message",
    [
        ('{"foo": "bar"}', '{"foo": "bar"}'),
        ('{"foo": "bar", "message": "error message"}', "error message"),
        ("<NOTAJSON", "<NOTAJSON"),
    ],
)
def test_message_parsing(mocker, error_body, expected_message, status, reason):
    """Test OCPError message parsing."""
    # mimic OCP lib ApiException
    mock_exception = mocker.Mock(status=status, reason=reason, body=error_body)
    error = OCPError.from_api_exception(mock_exception)
    assert isinstance(error, OCPError)
    assert error.status == status
    assert error.reason == reason
    assert error.message == expected_message


@pytest.fixture
def deployment_data():
    """Return data representing a Deployment."""
    return dict(
        kind="deployment",
        name="deployment",
        labels={"foo": "bar"},
        container_images=["some-image"],
        init_container_images=[],
    )


@pytest.fixture
def project_data():
    """Return data representing a Project."""
    return dict(
        name="some project",
        kind="namespace",
        labels={"foo": "bar"},
        deployments=[],
        errors=[],
    )


@pytest.mark.parametrize(
    "data,expected_class",
    [
        (pytest.lazy_fixture("deployment_data"), OCPDeployment),
        (pytest.lazy_fixture("project_data"), OCPProject),
    ],
)
def test_load_entity(data, expected_class):
    """Test load_entity function."""
    # protect data for future comparison
    expected_data = deepcopy(data)
    entity = load_entity(data)
    assert isinstance(entity, expected_class)
    assert expected_data == entity.to_dict()


class TestOCPBaseEntity:  # pylint: disable=missing-class-docstring, unused-variable
    """Test OCPBaseEntity and its inheritance side effects."""

    def test_kind_isnt_overridable(self):
        """Test kind attribute ins't overriden at instance level."""

        class TestEntity(OCPBaseEntity):
            kind = "not-overridable"
            name: str

        entity = TestEntity(kind="whatever", name="cool-name")
        assert entity.kind == "not-overridable"

    def test_missing_kind(self):
        """Test OCP entity missing 'kind' attribute."""
        with pytest.raises(
            NotImplementedError, match="SomeClass MUST implement an attribute 'kind'"
        ):

            class SomeClass(OCPBaseEntity):
                name: str

    def test_missing_type_annotations(self):
        """Test if OPC entity has type annotations."""
        with pytest.raises(AttributeError, match="don't have type annotations"):

            class SomeClass(OCPBaseEntity):
                kind = "whatever"

    def test_base_class_cant_be_initialized(self):
        """Test OCPBaseEntity behaves as if it is an ABC class."""
        with pytest.raises(TypeError, match="OCPBaseEntity can't be initialized."):
            OCPBaseEntity()

    def test_reused_kind(self):
        """Ensure kind can't be repeated."""

        class TestClass1(OCPBaseEntity):
            kind = "test-entity"
            name: str

        with pytest.raises(
            AssertionError, match="Entity with kind='test-entity' already registered."
        ):

            class TestClass2(OCPBaseEntity):
                kind = "test-entity"
                name: str
