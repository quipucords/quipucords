"""Test the environment utility."""

import os
from collections import namedtuple
from importlib.metadata import PackageNotFoundError
from unittest.mock import ANY, Mock, patch

import pytest
from django.test import TestCase

from quipucords import environment, release


@pytest.fixture(autouse=True)
def cleanup_server_version_cache():
    """Clean server version cache for these tests."""
    environment.server_version.cache_clear()


class EnvironmentTest(TestCase):
    """Tests against the environment functions."""

    @patch("os.environ")
    def test_commit_with_env(self, mock_os):
        """Test the commit method via environment."""
        expected = "buildnum"
        mock_os.get.return_value = expected
        result = environment.commit()
        self.assertEqual(result, expected)

    @patch("subprocess.check_output", return_value="buildnum".encode("utf-8"))
    def test_commit_with_subprocess(self, _patched_subprocess):
        """Test the commit method via subprocess."""
        result = environment.commit()
        self.assertEqual(result, "buildnum")

    @patch.dict(os.environ, {"QUIPUCORDS_COMMIT": "dummy-commit"})
    @patch("subprocess.check_output", side_effect=RuntimeError("STOP!"))
    def test_commit_with_envvar(self, _patched_subprocess):
        """Test the commit function using envvar."""
        result = environment.commit()
        self.assertEqual(result, "dummy-commit")

    @patch("platform.uname")
    def test_platform_info(self, mock_platform):
        """Test the platform_info method."""
        platform_record = namedtuple("Platform", ["os", "version"])
        a_plat = platform_record("Red Hat", "7.4")
        mock_platform.return_value = a_plat
        result = environment.platform_info()
        self.assertEqual(result["os"], "Red Hat")
        self.assertEqual(result["version"], "7.4")

    @patch("sys.version")
    def test_python_version(self, mock_sys_ver):
        """Test the python_version method."""
        expected = "Python 3.6"
        mock_sys_ver.replace.return_value = expected
        result = environment.python_version()
        self.assertEqual(result, expected)

    @patch("sys.modules")
    def test_modules(self, mock_modules):
        """Test the modules method."""
        expected = {"module1": "version1", "module2": "version2"}
        mod1 = Mock(__version__="version1")
        mod2 = Mock(__version__="version2")
        mock_modules.items.return_value = (("module1", mod1), ("module2", mod2))
        result = environment.modules()
        self.assertEqual(result, expected)

    @patch("quipucords.environment.logger.info")
    def test_startup(self, mock_logger):
        """Test the startup method."""
        environment.startup()
        mock_logger.assert_called_with(ANY, ANY)


@pytest.mark.parametrize(
    "package_version", [None, "unexpected_tag", PackageNotFoundError()]
)
def test_server_fallback_version(package_version):
    """Test the server fallback version."""
    release.infer_version.cache_clear()

    if isinstance(package_version, Exception):
        mock_kwargs = {"side_effect": package_version}
    else:
        mock_kwargs = {"return_value": package_version}

    expected = f"0.0.0+{environment.commit()}"

    with patch.object(release, "version", **mock_kwargs):
        assert expected == environment.server_version()
