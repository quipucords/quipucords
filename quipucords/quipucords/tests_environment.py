#
# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test the environment utility."""

from collections import namedtuple
from importlib.metadata import PackageNotFoundError
from unittest.mock import ANY, Mock, patch

import pytest
from django.test import TestCase

from . import environment, release


class EnvironmentTest(TestCase):
    """Tests against the environment functions."""

    @patch("os.environ")
    def test_commit_with_env(self, mock_os):
        """Test the commit method via environment."""
        expected = "buildnum"
        mock_os.get.return_value = expected
        result = environment.commit()
        self.assertEqual(result, expected)

    @patch("subprocess.check_output")
    def test_commit_with_subprocess(self, mock_subprocess):
        """Test the commit method via subprocess."""
        expected = "buildnum"
        mock_subprocess.return_value = expected
        result = environment.commit()
        self.assertEqual(result, expected)

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

    expected = f"0.0.0.{environment.commit()}"

    with patch.object(release, "version", **mock_kwargs):
        assert expected == environment.server_version()
