import os
import unittest
from unittest import mock

import pytest

from .featureflag import get_feature_flags_from_env, FeatureFlag


@pytest.mark.parametrize(
    "env_name,env_value,feature_name,feature_value",
    (("QPC_FEATURE_TEST", "0", "TEST", False),
     ("QPC_FEATURE_TEST", "1", "TEST", True)
     )
)
def test_get_feature_flags_from_env(env_name, env_value, feature_name, feature_value):
    """Tests if function retrieves new variables set in .env"""
    with mock.patch.dict(os.environ, {env_name: env_value}):
        dict_with_test_flags = get_feature_flags_from_env()
        assert feature_name in dict_with_test_flags
        assert dict_with_test_flags[feature_name] is feature_value


def test_if_returns_default_value_if_another_env_set():
    """Tests if function also returns variables in default dict if a new variable is set"""
    with mock.patch.dict(os.environ, ({"QPC_FEATURE_TEST": "0"})):
        dict_with_test_flags = get_feature_flags_from_env()
        assert "OVERALL_STATUS" in dict_with_test_flags
        assert "TEST" in dict_with_test_flags
        assert dict_with_test_flags["OVERALL_STATUS"] is False
        assert dict_with_test_flags["TEST"] is False


@pytest.mark.parametrize(
    "env_name,env_value,feature_name,feature_value",
    (("QPC_FEATURE_OVERALL_STATUS", "1", "OVERALL_STATUS", True),
     ("QPC_FEATURE_TEST", "0", "TEST", False)
     )
)
def test_if_value_for_env_default_list_gets_updated(env_name, env_value, feature_name, feature_value):
    """Tests if function updates env variable in default dict if a new value is set"""
    with mock.patch.dict(os.environ, ({env_name: env_value})):
        dict_with_test_flags = get_feature_flags_from_env()
        assert feature_name in dict_with_test_flags
        assert dict_with_test_flags[feature_name] is feature_value


def test_when_value_cant_be_cast_to_int():
    """Tests if function does not add or update key-values to default dict if value can`t be cast to int"""
    with mock.patch.dict(os.environ, ({"QPC_FEATURE_OVERALL_STATUS": "wrong"})):
        dict_with_test_flags = get_feature_flags_from_env()
        assert "OVERALL_STATUS" in dict_with_test_flags
        assert dict_with_test_flags["OVERALL_STATUS"] is False


@pytest.mark.parametrize(
    "env_name,env_value,feature_name",
    (("QPC_FEATURE_TEST", "10", "TEST"),
     ("QPC_FEATURE_TEST1", "3", "TEST1"),
     ("QPC_FEATURE_TEST2", "2000", "TEST2")
     )
)
def test_when_int_is_not_valid_value_for_env(env_name, env_value, feature_name):
    """Tests if function does not add values that are not present in the dict for valid env variables"""
    with mock.patch.dict(os.environ, ({env_name: env_value})):
        dict_with_test_flags = get_feature_flags_from_env()
        assert feature_name not in dict_with_test_flags


@pytest.mark.parametrize(
    "env_name,env_value,feature_name",
    (("TEST_QPC_FEATURE_", "1", "TEST"),
     ("TEST_QPC_FEATURE_", "1", "TEST_"),
     ("QPC_TEST1_FEATURE_", "0", "TEST1"),
     ("QPC_TEST1_FEATURE_", "0", "_TEST1"),
     ("QPC_TEST1_FEATURE_", "0", "TEST1_")
     )
)
def test_function_only_adds_names_follow_standard(env_name, env_value, feature_name):
    """Tests if function only adds variables that start with QPC_FEATURE_"""
    with mock.patch.dict(os.environ, ({env_name: env_value})):
        dict_with_test_flags = get_feature_flags_from_env()
        assert feature_name not in dict_with_test_flags


@pytest.mark.parametrize(
    "env_name,env_value,feature_name,feature_value",
    (("qpc_feature_test", "1", "TEST", True),
     ("qpc_feature_TEST1", "0", "TEST1", False),
     ("QPC_feature_TEST2", "0", "TEST2", False),
     ("qpc_FEATURE_test3", "1", "TEST3", True)
     )
)
def test_if_function_is_not_case_sensitive(env_name, env_value, feature_name, feature_value):
    """Tests if function is not case-sensitive and env names are stored following the standard"""
    with mock.patch.dict(os.environ, ({env_name: env_value})):
        dict_with_test_flags = get_feature_flags_from_env()
        assert feature_name in dict_with_test_flags
        assert dict_with_test_flags[feature_name] is feature_value


class TestFeatureFlag:

    @pytest.fixture
    def setup_feature_flag_instance_for_tests(self):
        with mock.patch.dict(os.environ, {"QPC_FEATURE_TEST": "1"}):
            dict_with_test_flags = get_feature_flags_from_env()
            feature_flag_instance = FeatureFlag(dict_with_test_flags)
            return feature_flag_instance

    def test_if_instance_contains_all_attributes(self, setup_feature_flag_instance_for_tests):
        """Tests if the constructor loads all attributes correctly"""
        assert hasattr(setup_feature_flag_instance_for_tests, "TEST")
        assert hasattr(setup_feature_flag_instance_for_tests, "OVERALL_STATUS")

    def test_if_instance_attributes_values_are_correct(self, setup_feature_flag_instance_for_tests):
        """Tests if the right values are attributed to the instance attributes"""
        assert setup_feature_flag_instance_for_tests.TEST is True
        assert setup_feature_flag_instance_for_tests.OVERALL_STATUS is False

    def test_is_feature_active(self, setup_feature_flag_instance_for_tests):
        """Tests method is_feature_active"""
        assert setup_feature_flag_instance_for_tests.is_feature_active("TEST") is True
        assert setup_feature_flag_instance_for_tests.is_feature_active("OVERALL_STATUS") is False
        with pytest.raises(ValueError):
            assert setup_feature_flag_instance_for_tests.is_feature_active("FALSE_ATTRIBUTE") is True


if __name__ == '__main__':
    unittest.main()
