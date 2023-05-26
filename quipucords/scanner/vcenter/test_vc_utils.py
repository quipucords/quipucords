"""Test the vcenter utils."""

from unittest.mock import ANY, Mock, patch

from django.test import TestCase

from api.models import Credential, ScanTask, Source, SourceOptions
from scanner.test_util import create_scan_job
from scanner.vcenter.utils import vcenter_connect


class VCenterUtilsTest(TestCase):
    """Tests VCenter utils functions."""

    def setUp(self):
        """Create test case setup."""
        self.cred = Credential(
            name="cred1",
            username="username",
            password="password",
            become_password=None,
            ssh_keyfile=None,
        )
        self.cred.save()

        options = SourceOptions(disable_ssl=True)
        options.save()

        self.source = Source(name="source1", port=22, hosts=["1.2.3.4"])
        self.source.options = options
        self.source.save()
        self.source.credentials.add(self.cred)

        self.scan_job, self.scan_task = create_scan_job(
            self.source, scan_type=ScanTask.SCAN_TYPE_INSPECT
        )

    def tearDown(self):
        """Cleanup test case setup."""

    def test_vcenter_connect(self):
        """Test the connection method."""
        mock_vcenter = Mock()
        with patch(
            "scanner.vcenter.utils.SmartConnectNoSSL", return_value=mock_vcenter
        ) as mock_smart_connect:
            vcenter = vcenter_connect(self.scan_task)
            self.assertEqual(mock_vcenter, vcenter)
            mock_smart_connect.assert_called_once_with(
                host=ANY, user=ANY, pwd=ANY, port=ANY
            )
