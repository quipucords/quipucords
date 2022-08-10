# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""Unit tests for the process module."""
from django.test import TestCase

from api.models import Credential, Scan, ScanJob, ScanTask, Source
from scanner.network.processing import process
from scanner.network.processing.util_for_test import ansible_result, ansible_results

HOST = "host"

NOT_A_KEY = "not_a_key"
NO_PROCESSOR_KEY = "no_processor_key"
TEST_KEY = "test_key"
DEPENDENT_KEY = "dependent_key"
PROCESSOR_ERROR_KEY = "processor_error_key"
NOT_TASK_RESULT_KEY = "not_task_result_key"


class TestIsSudoErrorValue(TestCase):
    """Test is_sudo_error_value."""

    def test_string_not_error(self):
        """A string that is not a sudo error."""
        self.assertFalse(process.is_sudo_error_value("foo"))

    def test_string_sudo_error(self):
        """A string with the sudo error value."""
        self.assertTrue(process.is_sudo_error_value(process.SUDO_ERROR))

    def test_list_not_error(self):
        """A list that is not a sudo error."""
        self.assertFalse(process.is_sudo_error_value(["foo"]))

    def test_list_sudo_error(self):
        """A list with the sudo error."""
        self.assertTrue(process.is_sudo_error_value([process.SUDO_ERROR]))

    def test_result_not_error(self):
        """An Ansible result that is not a sudo error."""
        self.assertFalse(process.is_sudo_error_value(ansible_result("foo")))

    def test_result_sudo_error(self):
        """An Ansible result that is a sudo error."""
        self.assertTrue(process.is_sudo_error_value(ansible_result(process.SUDO_ERROR)))


class TestIsAnsibleTaskResult(TestCase):
    """Test IsAnsibleTaskResult."""

    def test_not_dict(self):
        """A value that is not a dictionary."""
        self.assertFalse(process.is_ansible_task_result("foo"))

    def test_malformed_dict(self):
        """A dictionary with the wrong contents."""
        self.assertFalse(process.is_ansible_task_result({"a": "b"}))

    def test_skipped(self):
        """The result of a skipped task."""
        self.assertTrue(process.is_ansible_task_result({process.SKIPPED: True}))

    def test_ansible_result(self):
        """A single Ansible result."""
        self.assertTrue(process.is_ansible_task_result(ansible_result("a")))

    def test_with_items_result(self):
        """The result of a with_items task."""
        self.assertTrue(
            process.is_ansible_task_result(
                ansible_results(
                    [{"item": "a", "stdout": "a"}, {"item": "b", "stdout": "b"}]
                )
            )
        )


# pylint: disable=too-few-public-methods
class MyProcessor(process.Processor):
    """Basic test processor."""

    KEY = TEST_KEY

    @staticmethod
    def process(output, dependencies=None):
        """Return 1 to distinguish from MyDependentProcessor."""
        return 1


# pylint: disable=too-few-public-methods
class MyDependentProcessor(process.Processor):
    """Processor that depends on another key."""

    KEY = DEPENDENT_KEY
    DEPS = [NO_PROCESSOR_KEY]

    @staticmethod
    def process(output, dependencies=None):
        """Return 2 to distinguish from MyProcessor."""
        return 2


# pylint: disable=too-few-public-methods
class MyErroringProcessor(process.Processor):
    """Processor that has an internal error."""

    KEY = PROCESSOR_ERROR_KEY

    @staticmethod
    def process(output, dependencies=None):
        """Uh oh, this processor doesn't work."""
        raise Exception("Something went wrong!")


class TestProcess(TestCase):
    """Test the process() infrastructure."""

    def setUp(self):
        """Create test case setup."""
        self.cred = Credential(
            name="cred1",
            username="username",
            password="password",
            ssh_keyfile="keyfile",
            become_method="sudo",
            become_user="root",
            become_password="become",
        )
        self.cred.save()

        self.source = Source(name="source1", port=22)
        self.source.save()
        self.source.credentials.add(self.cred)

        self.source.hosts = '["1.2.3.4"]'
        self.source.save()

        # Create scan configuration
        scan = Scan(name="scan_name", scan_type=ScanTask.SCAN_TYPE_INSPECT)
        scan.save()

        # Add source to scan
        scan.sources.add(self.source)

        # Create Job
        self.scan_job = ScanJob(scan=scan)
        self.scan_job.save()

        self.scan_task = ScanTask(
            job=self.scan_job, source=self.source, scan_type=ScanTask.SCAN_TYPE_INSPECT
        )
        self.scan_task.save()

    def test_not_result_no_processing(self):
        """Test a value that is not a task result, and needs no processing."""
        self.assertEqual(
            process.process(self.scan_task, {}, NOT_TASK_RESULT_KEY, "foo", HOST), "foo"
        )

    def test_not_result_sudo_error(self):
        """Test a value that is not a task result, but is a sudo error."""
        self.assertEqual(
            process.process(
                self.scan_task, {}, NOT_TASK_RESULT_KEY, process.SUDO_ERROR, HOST
            ),
            process.NO_DATA,
        )

    def test_processing_bad_input(self):
        """Test a key that is not a task result, but needs processing."""
        self.assertEqual(
            process.process(self.scan_task, {}, TEST_KEY, "foo", HOST), process.NO_DATA
        )

    def test_no_processing(self):
        """Test a key that doesn't need to be processed."""
        self.assertEqual(
            process.process(
                self.scan_task, {}, NOT_A_KEY, ansible_result(process.NO_DATA), HOST
            ),
            ansible_result(process.NO_DATA),
        )

    def test_simple_processor(self):
        """Test a key whose processor succeeds."""
        self.assertEqual(
            process.process(
                self.scan_task, {}, TEST_KEY, ansible_result(process.NO_DATA), HOST
            ),
            1,
        )

    def test_missing_dependency(self):
        """Test a key whose processor is missing a dependency."""
        self.assertEqual(
            process.process(
                self.scan_task, {}, DEPENDENT_KEY, ansible_result(process.NO_DATA), HOST
            ),
            process.NO_DATA,
        )

    def test_satisfied_dependency(self):
        """Test a key whose processor has a dependency, which is present."""
        self.assertEqual(
            process.process(
                self.scan_task,
                {DEPENDENT_KEY: ansible_result("")},
                NO_PROCESSOR_KEY,
                "result",
                HOST,
            ),
            "result",
        )

    def test_skipped_task(self):
        """Test a task that Ansible skipped."""
        self.assertEqual(
            process.process(self.scan_task, {}, TEST_KEY, {"skipped": True}, HOST),
            process.NO_DATA,
        )

    def test_task_errored(self):
        """Test a task that errored on the remote machine."""
        self.assertEqual(
            process.process(
                self.scan_task, {}, TEST_KEY, ansible_result("error!", rc=1), HOST
            ),
            process.NO_DATA,
        )

    def test_processor_errored(self):
        """Test a task where the processor itself errors."""
        self.assertEqual(
            process.process(
                self.scan_task, {}, PROCESSOR_ERROR_KEY, ansible_result(""), HOST
            ),
            process.NO_DATA,
        )


class TestProcessorMeta(TestCase):
    """Test the ProcessorMeta class."""

    def test_must_have_key(self):
        """Require Processors to have a KEY."""
        with self.assertRaises(Exception):
            process.ProcessorMeta("NewProcessor", (), {})
