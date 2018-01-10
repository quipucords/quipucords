# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


"""Unit tests for initial processing."""

# pylint: disable=missing-docstring

import unittest
from scanner.network import initial_processing as ip


def ansible_result(stdout, rc=0):  # pylint: disable=invalid-name
    """Make an Ansible result dictionary for a successful result."""
    return {'rc': rc,
            'stdout': stdout,
            'stdout_lines': stdout.splitlines()}


def ansible_results(results):
    """Make an Ansible result dictionary for a with_items task."""
    return {'results':
            [{'item': result['item'],
              'stdout': result['stdout'],
              'stdout_lines': result['stdout'].splitlines(),
              'rc': result.get('rc', 0)}
             for result in results]}


NOT_A_KEY = 'not_a_key'
NO_PROCESSOR_KEY = 'no_processor_key'
TEST_KEY = 'test_key'
DEPENDENT_KEY = 'dependent_key'
PROCESSOR_ERROR_KEY = 'processor_error_key'
INPUT_ERROR_KEY = 'input_error_key'


# pylint: disable=too-few-public-methods
class MyProcessor(ip.Processor):
    """Basic test processor."""

    KEY = TEST_KEY

    @staticmethod
    def process(output):
        """Return 1 to distinguish from MyDependentProcessor."""
        return 1


# pylint: disable=too-few-public-methods
class MyDependentProcessor(ip.Processor):
    """Processor that depends on another key."""

    KEY = DEPENDENT_KEY
    DEPS = [NO_PROCESSOR_KEY]

    @staticmethod
    def process(output):
        """Return 2 to distinguish from MyProcessor."""
        return 2


# pylint: disable=too-few-public-methods
class MyErroringProcessor(ip.Processor):
    """Processor that has an internal error."""

    KEY = PROCESSOR_ERROR_KEY

    @staticmethod
    def process(output):
        """Uh oh, this processor doesn't work."""
        raise Exception('Something went wrong!')


# pylint: disable=too-few-public-methods
class MyInputErrorProcessor(ip.Processor):
    """Processor that reports an input error."""

    KEY = INPUT_ERROR_KEY

    @staticmethod
    def process(output):
        """Report bad input."""
        return Exception('bad input!')


class TestProcess(unittest.TestCase):
    """Test the process() infrastructure."""

    def test_no_processing(self):
        """Test a key that doesn't need to be processed."""
        self.assertEqual(
            ip.process({NOT_A_KEY: ansible_result('')}),
            {NOT_A_KEY: ansible_result('')})

    def test_simple_processor(self):
        """Test a key whose processor succeeds."""
        self.assertEqual(
            ip.process({TEST_KEY: ansible_result('')}),
            {TEST_KEY: '1'})

    def test_missing_dependency(self):
        """Test a key whose processor is missing a dependency."""
        self.assertEqual(
            ip.process({DEPENDENT_KEY: ansible_result('')}),
            {DEPENDENT_KEY:
             'Error: dependent_key missing dependency no_processor_key'})

    def test_satisfied_dependency(self):
        """Test a key whose processor has a dependency, which is present."""
        self.assertEqual(
            ip.process({NO_PROCESSOR_KEY: 'result',
                        DEPENDENT_KEY: ansible_result('')}),
            {NO_PROCESSOR_KEY: 'result',
             DEPENDENT_KEY: '2'})

    def test_skipped_task(self):
        """Test a task that Ansible skipped."""
        self.assertEqual(
            ip.process({TEST_KEY: {'skipped': True}}),
            {TEST_KEY: 'Error: test_key skipped, no results'})

    def test_task_errored(self):
        """Test a task that errored on the remote machine."""
        self.assertEqual(
            ip.process({TEST_KEY: ansible_result('error!', rc=1)}),
            {TEST_KEY: 'Error: remote command returned error!'})

    def test_processor_errored(self):
        """Test a task where the processor itself errors."""
        value = ip.process({PROCESSOR_ERROR_KEY: ansible_result('')})
        self.assertIn(PROCESSOR_ERROR_KEY, value)
        print('test_processor_errored:', value)
        self.assertTrue(
            value[PROCESSOR_ERROR_KEY].startswith('Error: processor returned'))

    def test_input_error(self):
        """Test a task where the processor rejects the remote results."""
        self.assertEqual(
            ip.process({INPUT_ERROR_KEY: ansible_result('')}),
            {INPUT_ERROR_KEY: 'Error: bad input!'})


class TestProcessorMeta(unittest.TestCase):
    def test_must_have_key(self):
        with self.assertRaises(Exception):
            ProcessorMeta('NewProcessor', (), {})


class TestProcessJbossEapRunningPaths(unittest.TestCase):
    def test_success_case(self):
        self.assertEqual(
            ip.ProcessJbossEapRunningPaths.process(ansible_result(' good ')),
            'good')

    def test_find_warning(self):
        self.assertIsInstance(
            ip.ProcessJbossEapRunningPaths.process(
                ansible_result(ip.FIND_WARNING)),
            Exception)


class TestProcessFindJboss(unittest.TestCase):
    def test_success_case(self):
        self.assertEqual(
            ip.ProcessFindJboss.process(ansible_result('a\nb\nc')),
            ['a', 'b', 'c'])


class TestProcessIdUJboss(unittest.TestCase):
    """Tests for 'id -u jboss'."""

    def test_user_found(self):
        """'id' found the user."""
        self.assertEqual(
            ip.ProcessIdUJboss.process(ansible_result('11111')),
            True)

    def test_no_such_user(self):
        """'id' did not find the user."""
        self.assertEqual(
            ip.ProcessIdUJboss.process(
                ansible_result('id: jboss: no such user', rc=1)),
            False)

    def test_unknown_error(self):
        """'id' returned an error."""
        self.assertIsInstance(
            ip.ProcessIdUJboss.process(
                ansible_result('something went wrong!', rc=1)),
            Exception)


class TestProcessJbossCommonFiles(unittest.TestCase):
    """Test looking for common jboss files."""

    def test_three_states(self):
        """Test one file found, one not found, and one skipped."""
        self.assertEqual(
            ip.ProcessJbossEapCommonFiles.process(
                {'results': [
                    {'item': 'dir1',
                     'skipped': True},
                    {'item': 'dir2',
                     'rc': 1},
                    {'item': 'dir3',
                     'rc': 0}]}),
            ['dir3'])


class TestProcessJbossEapProcesses(unittest.TestCase):
    """Test looking for JBoss EAP processes."""

    def test_no_processes(self):
        """No processes found."""
        self.assertEqual(
            ip.ProcessJbossEapProcesses.process(ansible_result('', rc=1)),
            0)

    def test_found_processes(self):
        """Found one process."""
        self.assertEqual(
            ip.ProcessJbossEapProcesses.process(ansible_result('1\n2\n3')),
            1)

    def test_bad_data(self):
        """Found too few processes."""
        self.assertIsInstance(
            ip.ProcessJbossEapProcesses.process(ansible_result('1')),
            Exception)


class TestProcessJbossEapPackages(unittest.TestCase):
    """Test looking for JBoss EAP rpm packages."""

    def test_found_packages(self):
        """Found some packages."""
        self.assertEqual(
            ip.ProcessJbossEapPackages.process(ansible_result('a\nb\nc')),
            3)

    def test_no_packages(self):
        """No RPMs found."""
        self.assertEqual(
            ip.ProcessJbossEapPackages.process(ansible_result('')),
            0)


class TestProcessJbossLocateJbossModulesJar(unittest.TestCase):
    """Test using locate to find jboss-modules.jar."""

    def test_success(self):
        """Found jboss-modules.jar."""
        self.assertEqual(
            ip.ProcessJbossEapLocate.process(ansible_result('a\nb\nc')),
            ['a', 'b', 'c'])

    def test_not_found(self):
        """Did not find jboss-modules.jar."""
        self.assertEqual(
            ip.ProcessJbossEapLocate.process(ansible_result('')),
            [])


class TestProcessEapHomeLs(unittest.TestCase):
    """Test listing EAP_HOME directories."""

    def test_three_states(self):
        """A directory can go three ways."""
        extra_files = [
            'docs', 'installation', 'LICENSE.txt', 'welcome-content', 'bin',
            'domain', 'Uninstaller', 'bundles', 'icons', 'SHA256SUM']

        self.assertEqual(
            ip.ProcessEapHomeLs.process(
                ansible_results([
                    # dir1: ls was successful, directory has JBoss files.
                    {'item': 'dir1',
                     'stdout':
                     '\n'.join(extra_files +
                               ip.ProcessEapHomeLs.INDICATOR_FILES)},
                    # dir2: ls was unsuccessful. Output should be ignored.
                    {'item': 'dir2',
                     'rc': 1,
                     'stdout': '\n'.join(ip.ProcessEapHomeLs.INDICATOR_FILES)},
                    # dir3: ls was successful, directory has no JBoss files.
                    {'item': 'dir3',
                     'stdout': '\n'.join(extra_files)}])),
            {'dir1': ip.ProcessEapHomeLs.INDICATOR_FILES,
             'dir2': [],
             'dir3': []})


class TestProcessEapHomeCat(unittest.TestCase):
    """Test scanning the contents of $EAP_HOME/version.txt."""

    cat_result = (
        'Red Hat JBoss Enterprise Application Platform - Version 6.4.0.GA')

    def test_three_dirs(self):
        """A directory can have three outcomes."""
        self.assertEqual(
            ip.ProcessEapHomeCat.process(
                ansible_results([
                    # dir1: cat was successful, stdout has 'Red Hat' in it.
                    {'item': 'dir1', 'stdout': self.cat_result},
                    # dir2: cat was unsuccessful. Output should be ignored.
                    {'item': 'dir2', 'rc': 1, 'stdout': self.cat_result},
                    # dir3: cat was successful, output does not have 'Red Hat'.
                    {'item': 'dir3', 'stdout': 'foo'}])),
            {'dir1': True,
             'dir2': False,
             'dir3': False})


class TestProcessJbossEapInitFiles(unittest.TestCase):
    """Test looking for 'jboss' or 'eap' init files."""

    processors = [ip.ProcessJbossEapChkconfig,
                  ip.ProcessJbossEapSystemctl]

    def test_no_jboss(self):
        """No 'jboss' or 'eap' found."""
        for processor in self.processors:
            self.assertEqual(
                # Blank line in input to check that processor will skip it.
                processor.process(ansible_result('foo\nbar\n\nbaz')),
                [])

    def test_jboss(self):
        """'jboss' found."""
        # This tests that the processor returns the 'jboss bar' line
        # and that it does *not* return the 'baz jboss' line, becuase
        # in that line 'jboss' is not in the first piece.
        for processor in self.processors:
            self.assertEqual(
                processor.process(
                    ansible_result('  foo\n  jboss bar\n  baz jboss')),
                ['jboss bar'])

    def test_eap(self):
        """'eap' found."""
        for processor in self.processors:
            self.assertEqual(
                processor.process(
                    ansible_result('  foo\n  eap bar\n  baz eap')),
                ['eap bar'])
