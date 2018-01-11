# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""Unit tests for the process module."""

import unittest
from scanner.network.processing import process
from scanner.network.processing.test_util import ansible_result

NOT_A_KEY = 'not_a_key'
NO_PROCESSOR_KEY = 'no_processor_key'
TEST_KEY = 'test_key'
DEPENDENT_KEY = 'dependent_key'
PROCESSOR_ERROR_KEY = 'processor_error_key'


# pylint: disable=too-few-public-methods
class MyProcessor(process.Processor):
    """Basic test processor."""

    KEY = TEST_KEY

    @staticmethod
    def process(output):
        """Return 1 to distinguish from MyDependentProcessor."""
        return 1


# pylint: disable=too-few-public-methods
class MyDependentProcessor(process.Processor):
    """Processor that depends on another key."""

    KEY = DEPENDENT_KEY
    DEPS = [NO_PROCESSOR_KEY]

    @staticmethod
    def process(output):
        """Return 2 to distinguish from MyProcessor."""
        return 2


# pylint: disable=too-few-public-methods
class MyErroringProcessor(process.Processor):
    """Processor that has an internal error."""

    KEY = PROCESSOR_ERROR_KEY

    @staticmethod
    def process(output):
        """Uh oh, this processor doesn't work."""
        raise Exception('Something went wrong!')


class TestProcess(unittest.TestCase):
    """Test the process() infrastructure."""

    def test_no_processing(self):
        """Test a key that doesn't need to be processed."""
        self.assertEqual(
            process.process({NOT_A_KEY: ansible_result('')}),
            {NOT_A_KEY: ansible_result('')})

    def test_simple_processor(self):
        """Test a key whose processor succeeds."""
        self.assertEqual(
            process.process({TEST_KEY: ansible_result('')}),
            {TEST_KEY: '1'})

    def test_missing_dependency(self):
        """Test a key whose processor is missing a dependency."""
        self.assertEqual(
            process.process({DEPENDENT_KEY: ansible_result('')}),
            {DEPENDENT_KEY: process.NO_DATA})

    def test_satisfied_dependency(self):
        """Test a key whose processor has a dependency, which is present."""
        self.assertEqual(
            process.process({NO_PROCESSOR_KEY: 'result',
                             DEPENDENT_KEY: ansible_result('')}),
            {NO_PROCESSOR_KEY: 'result',
             DEPENDENT_KEY: '2'})

    def test_skipped_task(self):
        """Test a task that Ansible skipped."""
        self.assertEqual(
            process.process({TEST_KEY: {'skipped': True}}),
            {TEST_KEY: process.NO_DATA})

    def test_task_errored(self):
        """Test a task that errored on the remote machine."""
        self.assertEqual(
            process.process({TEST_KEY: ansible_result('error!', rc=1)}),
            {TEST_KEY: process.NO_DATA})

    def test_processor_errored(self):
        """Test a task where the processor itself errors."""
        self.assertEqual(
            process.process({PROCESSOR_ERROR_KEY: ansible_result('')}),
            {PROCESSOR_ERROR_KEY: process.NO_DATA})


class TestProcessorMeta(unittest.TestCase):
    """Test the ProcessorMeta class."""

    def test_must_have_key(self):
        """Require Processors to have a KEY."""
        with self.assertRaises(Exception):
            process.ProcessorMeta('NewProcessor', (), {})
