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
from pydantic import ValidationError  # pylint: disable=no-name-in-module

from scanner.openshift.entities import (
    MEMORY_CONVERSION_ERROR,
    NodeResources,
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
        errors={},
    )


@pytest.fixture
def project_with_deployment(project_data, deployment_data):
    """Return data representing a project + deployments."""
    project_data["deployments"] = [deployment_data]
    return project_data


def test_load_nested(project_with_deployment):
    """Test loading entity with other nested entities."""
    entity = load_entity(project_with_deployment)
    assert isinstance(entity, OCPProject)
    assert isinstance(entity.deployments, list)
    assert isinstance(entity.deployments[0], OCPDeployment)


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
    assert expected_data == entity.dict()


class TestOCPBaseEntity:  # pylint: disable=missing-class-docstring, unused-variable
    """Test OCPBaseEntity and its inheritance side effects."""

    def test_kind_isnt_overridable(self):
        """Test kind attribute ins't overriden at instance level."""

        class TestEntity(OCPBaseEntity):
            _kind = "not-overridable"
            name: str

        entity = TestEntity(kind="whatever", name="cool-name")
        assert entity.kind == "not-overridable"

    def test_missing_kind(self):
        """Test OCP entity missing '_kind' attribute."""
        with pytest.raises(
            NotImplementedError, match="SomeClass MUST implement an attribute '_kind'"
        ):

            class SomeClass(OCPBaseEntity):
                name: str

    def test_reused_kind(self):
        """Ensure kind can't be repeated."""

        class TestClass1(OCPBaseEntity):
            _kind = "test-entity"
            name: str

        with pytest.raises(
            AssertionError, match="Entity with kind='test-entity' already registered."
        ):

            class TestClass2(OCPBaseEntity):
                _kind = "test-entity"
                name: str

    def test_kind_is_available_to_subclass(self):
        """Ensure kind is available on entity."""

        class TestClass(OCPBaseEntity):
            _kind = "test-available-to-subclass"
            name: str

        entity = TestClass(name="foo")
        assert entity.kind is not None


@pytest.mark.parametrize(
    "value, expected_result, attr_value",
    [
        ("200m", 0.2, 0.2),
        ("3500m", 3.5, 3.5),
        (2.0, 2.0, 2.0),
        (4, 4.0, 4.0),
        ("2", "2", 2.0),
    ],
)
# pylint: disable=no-value-for-parameter, protected-access
def test_cpu_validator_with_convertible_values(value, expected_result, attr_value):
    """Ensure cpu data is being converted appropriately."""
    converted_value = NodeResources._convert_cpu_value(value)
    assert converted_value == expected_result

    node_resource = NodeResources(cpu=value)
    assert node_resource.cpu == attr_value


@pytest.mark.parametrize(
    "value",
    ["cpu_value", [2.0], "200k", {"cpu_value": "3500m"}],
)
def test_cpu_validator_with_inappropriate_values(value):
    """Ensure proper error is being raised for values that belong to wrong data type."""
    with pytest.raises(ValidationError) as error_info:
        NodeResources(cpu=value)
    assert "value is not a valid float" in str(error_info.value)


@pytest.mark.parametrize(
    "value, expected_result",
    [
        ("1Ki", 1024),
        ("1K", 1000),
        ("10Gi", 10737418240),
        ("1P", 1000000000000000),
        ("150Mi", 157286400),
        (123, 123),
    ],
)
# pylint: disable=no-value-for-parameter, protected-access
def test_memory_validator_with_convertible_values(value, expected_result):
    """Ensure memory data is being converted appropriately."""
    converted_value = NodeResources._convert_memory_bytes(value)
    assert converted_value == expected_result

    node_resources = NodeResources(memory_in_bytes=value)
    assert node_resources.memory_in_bytes == expected_result


@pytest.mark.parametrize(
    "value",
    ["15000GI", "15000L", "1500mi"],
)
# pylint: disable=no-value-for-parameter, protected-access
def test_memory_validator_with_uncovertible_values(value):
    """Ensure proper error is being raised for values that can't be converted."""
    with pytest.raises(ValueError, match=MEMORY_CONVERSION_ERROR):
        NodeResources._convert_memory_bytes(value)


@pytest.mark.parametrize(
    "value",
    [[2.0], {"memory_value": "15500Ki"}, ("1500Ki",)],
)
def test_memory_validator_with_inappropriate_values(value):
    """Ensure proper error is being raised for wrong data types."""
    with pytest.raises(ValidationError) as exc_info:
        NodeResources(memory_in_bytes=value)
    assert "value is not a valid integer" in str(exc_info.value)
