"""Test the vcenter utils."""

from unittest.mock import ANY, Mock, patch

import pytest

from api.models import Credential, ScanTask, Source
from scanner.vcenter.utils import vcenter_connect
from tests.scanner.test_util import create_scan_job


@pytest.mark.django_db
class TestVCenterUtilsTest:
    """Tests VCenter utils functions."""

    def setup_method(self, _test_method):
        """Create test case setup."""
        self.cred = Credential(
            name="cred1",
            username="username",
            password="password",
            become_password=None,
            ssh_keyfile=None,
        )
        self.cred.save()

        self.source = Source(
            name="source1", port=22, hosts=["1.2.3.4"], disable_ssl=True
        )
        self.source.save()
        self.source.credentials.add(self.cred)

        self.scan_job, self.scan_task = create_scan_job(
            self.source, scan_type=ScanTask.SCAN_TYPE_INSPECT
        )

    def test_vcenter_connect(self):
        """Test the connection method."""
        mock_vcenter = Mock()
        with patch(
            "scanner.vcenter.utils.SmartConnectNoSSL", return_value=mock_vcenter
        ) as mock_smart_connect:
            vcenter = vcenter_connect(self.scan_task)
            assert mock_vcenter == vcenter
            mock_smart_connect.assert_called_once_with(
                host=ANY, user=ANY, pwd=ANY, port=ANY
            )
