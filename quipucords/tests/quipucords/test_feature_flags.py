"""Test the FeatureFlag class and helper function."""

import os
from unittest import mock

import pytest

from quipucords.featureflag import FeatureFlag


@pytest.mark.parametrize(
    "env_name,env_value,feature_name,feature_value",
    (
        ("QPC_FEATURE_TEST", "0", "TEST", False),
        ("QPC_FEATURE_TEST", "1", "TEST", True),
    ),
)
def test_get_feature_flags_from_env(env_name, env_value, feature_name, feature_value):
    """Tests if function retrieves new variables set in .env."""
    with mock.patch.dict(os.environ, {env_name: env_value}):
        dict_with_test_flags = FeatureFlag.get_feature_flags_from_env()
        assert feature_name in dict_with_test_flags
        assert dict_with_test_flags[feature_name] is feature_value


def test_if_returns_default_value_if_another_env_set():
    """Tests if function also returns variables in default dict."""
    with mock.patch.dict(os.environ, ({"QPC_FEATURE_TEST": "0"})):
        dict_with_test_flags = FeatureFlag.get_feature_flags_from_env()
        assert "OCP_WORKLOADS" in dict_with_test_flags
        assert "TEST" in dict_with_test_flags
        assert dict_with_test_flags["OCP_WORKLOADS"] is False
        assert dict_with_test_flags["TEST"] is False


@pytest.mark.parametrize(
    "env_name,env_value,feature_name,feature_value",
    (
        ("QPC_FEATURE_OCP_WORKLOADS", "1", "OCP_WORKLOADS", True),
        ("QPC_FEATURE_TEST", "0", "TEST", False),
    ),
)
def test_if_value_for_env_default_list_gets_updated(
    env_name, env_value, feature_name, feature_value
):
    """Tests if function updates env variable in default."""
    with mock.patch.dict(os.environ, ({env_name: env_value})):
        dict_with_test_flags = FeatureFlag.get_feature_flags_from_env()
        assert feature_name in dict_with_test_flags
        assert dict_with_test_flags[feature_name] is feature_value


def test_when_value_cant_be_cast_to_int():
    """Tests if function only updates values if it can be cast to int."""
    with mock.patch.dict(
        os.environ, ({"QPC_FEATURE_OVERALL_STATUS": "wrong"})
    ), pytest.raises(ValueError) as exc:
        FeatureFlag.get_feature_flags_from_env()
    assert (
        str(exc.value) == "'wrong' from 'QPC_FEATURE_OVERALL_STATUS'"
        " can't be converted to int, verify your"
        " environment variables."
    )


@pytest.mark.parametrize(
    "env_name,env_value",
    (
        ("QPC_FEATURE_TEST", "10"),
        ("QPC_FEATURE_TEST1", "3"),
        ("QPC_FEATURE_TEST2", "2000"),
    ),
)
def test_when_int_is_not_valid_value_for_env(
    env_name,
    env_value,
):
    """Test when int is not a valid value for env."""
    with mock.patch.dict(os.environ, ({env_name: env_value})), pytest.raises(
        ValueError, match="can't be converted to int"
    ):
        FeatureFlag.get_feature_flags_from_env()


@pytest.mark.parametrize(
    "env_name,env_value,feature_name",
    (
        ("TEST_QPC_FEATURE_", "1", "TEST"),
        ("TEST_QPC_FEATURE_", "1", "TEST_"),
        ("QPC_TEST1_FEATURE_", "0", "TEST1"),
        ("QPC_TEST1_FEATURE_", "0", "_TEST1"),
        ("QPC_TEST1_FEATURE_", "0", "TEST1_"),
    ),
)
def test_function_only_adds_names_follow_standard(env_name, env_value, feature_name):
    """Tests if function only adds variables that start with QPC_FEATURE_."""
    with mock.patch.dict(os.environ, ({env_name: env_value})):
        dict_with_test_flags = FeatureFlag.get_feature_flags_from_env()
        assert feature_name not in dict_with_test_flags


@pytest.mark.parametrize(
    "env_name,env_value,feature_name,feature_value",
    (
        ("qpc_feature_test", "1", "TEST", True),
        ("qpc_feature_TEST1", "0", "TEST1", False),
        ("QPC_feature_TEST2", "0", "TEST2", False),
        ("qpc_FEATURE_test3", "1", "TEST3", True),
    ),
)
def test_if_function_is_not_case_sensitive(
    env_name, env_value, feature_name, feature_value
):
    """Tests if function is not case-sensitive."""
    with mock.patch.dict(os.environ, ({env_name: env_value})):
        dict_with_test_flags = FeatureFlag.get_feature_flags_from_env()
        assert feature_name in dict_with_test_flags
        assert dict_with_test_flags[feature_name] is feature_value


@pytest.fixture
def setup_feature_flag_instance_for_tests():
    """Set up instance of FeatureFlag class for tests."""
    with mock.patch.dict(os.environ, {"QPC_FEATURE_TEST": "1"}):
        feature_flag_instance = FeatureFlag()
        return feature_flag_instance


def test_if_instance_contains_all_attributes(
    setup_feature_flag_instance_for_tests,
):
    """Tests if the constructor loads all attributes correctly."""
    assert hasattr(setup_feature_flag_instance_for_tests, "TEST")
    assert hasattr(setup_feature_flag_instance_for_tests, "OCP_WORKLOADS")


def test_if_instance_attributes_values_are_correct(
    setup_feature_flag_instance_for_tests,
):
    """Tests if the right values are attributed to attribute."""
    assert setup_feature_flag_instance_for_tests.TEST is True
    assert setup_feature_flag_instance_for_tests.OCP_WORKLOADS is False


def test_is_feature_active(setup_feature_flag_instance_for_tests):
    """Tests method is_feature_active."""
    assert setup_feature_flag_instance_for_tests.is_feature_active("TEST") is True
    assert (
        setup_feature_flag_instance_for_tests.is_feature_active("OCP_WORKLOADS")
        is False
    )

    with pytest.raises(ValueError):
        setup_feature_flag_instance_for_tests.is_feature_active("FALSE_ATTRIBUTE")


def test_as_dict(setup_feature_flag_instance_for_tests):
    """Tests method as_dict."""
    assert isinstance(setup_feature_flag_instance_for_tests.as_dict(), dict)
    assert setup_feature_flag_instance_for_tests.as_dict()["OCP_WORKLOADS"] is False
    assert setup_feature_flag_instance_for_tests.as_dict()["TEST"] is True
