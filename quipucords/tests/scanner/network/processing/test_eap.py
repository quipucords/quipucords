"""Unit tests for initial processing."""

# pylint: disable=missing-docstring

import unittest

from scanner.network.processing import eap, process
from scanner.network.processing.util_for_test import (
    ansible_item,
    ansible_result,
    ansible_results,
)


class TestProcessJbossEapRunningPaths(unittest.TestCase):
    """Test ProcessJbossEapRunningPaths."""

    def test_success_case(self):
        """Strip spaces from good input."""
        self.assertEqual(
            eap.ProcessJbossEapRunningPaths.process(ansible_result(" good ")), ["good"]
        )

    def test_find_warning(self):
        """Fail if we get the special find warning string."""
        self.assertEqual(
            eap.ProcessJbossEapRunningPaths.process(ansible_result(eap.FIND_WARNING)),
            process.NO_DATA,
        )


class TestProcessFindJboss(unittest.TestCase):
    """Test ProcessFindJBoss."""

    def test_success_case(self):
        """Return stdout_lines in case of success."""
        self.assertEqual(
            eap.ProcessFindJboss.process(ansible_result("a\nb\nc")), ["a", "b", "c"]
        )


class TestProcessIdUJboss(unittest.TestCase):
    """Tests for 'id -u jboss'."""

    def test_user_found(self):
        """'id' found the user."""
        self.assertEqual(eap.ProcessIdUJboss.process(ansible_result("11111")), True)

    def test_no_such_user(self):
        """'id' did not find the user."""
        self.assertEqual(
            eap.ProcessIdUJboss.process(
                ansible_result("id: jboss: no such user", rc=1)
            ),
            False,
        )

    def test_unknown_error(self):
        """'id' returned an error."""
        self.assertEqual(
            eap.ProcessIdUJboss.process(ansible_result("something went wrong!", rc=1)),
            process.NO_DATA,
        )


class TestProcessJbossCommonFiles(unittest.TestCase):
    """Test looking for common jboss files."""

    def test_three_states(self):
        """Test one file found, one not found, and one skipped."""
        self.assertEqual(
            eap.ProcessJbossEapCommonFiles.process(
                {
                    "results": [
                        {"item": "dir1", "skipped": True},
                        {"item": "dir2", "rc": 1},
                        {"item": "dir3", "rc": 0},
                    ]
                }
            ),
            ["dir3"],
        )


class TestProcessJbossProcesses(unittest.TestCase):
    """Test looking for JBoss processes."""

    def test_no_processes(self):
        """No processes found."""
        self.assertEqual(eap.ProcessJbossProcesses.process(ansible_result("")), 0)

    def test_found_processes(self):
        """Found one process."""
        self.assertEqual(
            eap.ProcessJbossProcesses.process(ansible_result("java\nbash\ngrep")), 1
        )

    def test_no_grep(self):
        """Grep sometimes doesn't appear in the ps output."""
        self.assertEqual(
            eap.ProcessJbossProcesses.process(ansible_result("java\nbash")), 1
        )

    def test_bad_rc(self):
        """Test that a bad return code returns 0 processes."""
        self.assertEqual(eap.ProcessJbossProcesses.process({"results": [{"rc": 1}]}), 0)


class TestProcessJbossEapPackages(unittest.TestCase):
    """Test looking for JBoss EAP rpm packages."""

    def test_found_packages(self):
        """Found some packages."""
        self.assertEqual(
            eap.ProcessJbossEapPackages.process(ansible_result("a\nb\nc")), 3
        )

    def test_no_packages(self):
        """No RPMs found."""
        self.assertEqual(eap.ProcessJbossEapPackages.process(ansible_result("")), 0)


class TestProcessJbossLocateJbossModulesJar(unittest.TestCase):
    """Test using locate to find jboss-modules.jar."""

    def test_success(self):
        """Found jboss-modules.jar."""
        self.assertEqual(
            eap.ProcessJbossEapLocate.process(ansible_result("a\nb\nc")),
            ["a", "b", "c"],
        )

    def test_not_found(self):
        """Did not find jboss-modules.jar."""
        self.assertEqual(eap.ProcessJbossEapLocate.process(ansible_result("")), [])


class TestProcessEapHomeLs(unittest.TestCase):
    """Test listing EAP_HOME directories."""

    def test_three_states(self):
        """A directory can go three ways."""
        extra_files = [
            "docs",
            "installation",
            "LICENSE.txt",
            "welcome-content",
            "bin",
            "domain",
            "Uninstaller",
            "bundles",
            "icons",
            "SHA256SUM",
        ]

        self.assertEqual(
            eap.ProcessEapHomeLs.process(
                ansible_results(
                    [
                        # dir1: ls was successful, directory has JBoss files.
                        {
                            "item": "dir1",
                            "stdout": "\n".join(
                                extra_files + eap.ProcessEapHomeLs.INDICATOR_FILES
                            ),
                        },
                        # dir2: ls was unsuccessful. Output should be ignored.
                        {
                            "item": "dir2",
                            "rc": 1,
                            "stdout": "\n".join(eap.ProcessEapHomeLs.INDICATOR_FILES),
                        },
                        # dir3: ls was successful, directory has no JBoss files.
                        {"item": "dir3", "stdout": "\n".join(extra_files)},
                    ]
                )
            ),
            {"dir1": eap.ProcessEapHomeLs.INDICATOR_FILES, "dir2": [], "dir3": []},
        )


class TestProcessEapHomeVersionTxt(unittest.TestCase):
    """Test scanning the contents of $EAP_HOME/version.txt."""

    cat_result = "Red Hat JBoss Enterprise Application Platform - Version 6.4.0.GA"

    def test_three_dirs(self):
        """A directory can have three outcomes."""
        self.assertEqual(
            eap.ProcessEapHomeVersionTxt.process(
                ansible_results(
                    [
                        # dir1: cat was successful, stdout has 'Red Hat' in it.
                        {"item": "dir1", "stdout": self.cat_result},
                        # dir2: cat was unsuccessful. Output should be ignored.
                        {"item": "dir2", "rc": 1, "stdout": self.cat_result},
                        # dir3: cat was successful, output does not have 'Red Hat'.
                        {"item": "dir3", "stdout": "foo"},
                    ]
                )
            ),
            {"dir1": "6.4.0", "dir2": False, "dir3": "foo"},
        )


class TestProcessJbossEapInitFiles(unittest.TestCase):
    """Test looking for 'jboss' or 'eap' init files."""

    processors = [eap.ProcessJbossEapChkconfig, eap.ProcessJbossEapSystemctl]

    def test_no_jboss(self):
        """No 'jboss' or 'eap' found."""
        for processor in self.processors:
            self.assertEqual(
                # Blank line in input to check that processor will skip it.
                processor.process(ansible_result("foo\nbar\n\nbaz")),
                [],
            )

    def test_jboss(self):
        """'jboss' found."""
        # This tests that the processor returns the 'jboss bar' line
        # and that it does *not* return the 'baz jboss' line, becuase
        # in that line 'jboss' is not in the first piece.
        for processor in self.processors:
            self.assertEqual(
                processor.process(ansible_result("  foo\n  jboss bar\n  baz jboss")),
                ["jboss bar"],
            )

    def test_eap(self):
        """'eap' found."""
        for processor in self.processors:
            self.assertEqual(
                processor.process(ansible_result("  foo\n  eap bar\n  baz eap")),
                ["eap bar"],
            )


class TestProcessEapHomeBinForFuse(unittest.TestCase):
    """Test looking for fuse scripts."""

    def test_fuse_not_found(self):
        """Test failure to find a fuse script."""
        found_files = ["foo.sh", "README"]

        processor_input = ansible_results(
            [{"item": "/some/dir", "stdout": "\n".join(found_files)}]
        )
        expected_result = {"/some/dir": []}
        actual_result = eap.ProcessEapHomeBinForFuse.process(processor_input)
        self.assertEqual(actual_result, expected_result)

    def test_fuse_is_found(self):
        """Test successfully finding a fuse script."""
        found_files = [
            "foo.sh",
            "README",
        ] + eap.ProcessEapHomeBinForFuse.INDICATOR_FILES[:-1]
        processor_input = ansible_results(
            [{"item": "/some/dir", "stdout": "\n".join(found_files)}]
        )
        expected_result = {
            "/some/dir": eap.ProcessEapHomeBinForFuse.INDICATOR_FILES[:-1]
        }
        actual_result = eap.ProcessEapHomeBinForFuse.process(processor_input)
        self.assertEqual(actual_result, expected_result)


class TestItemSuccessChecker(unittest.TestCase):
    """Test looking for eap home layers."""

    def test_success(self):
        """Found eap home layers."""
        self.assertEqual(
            eap.ItemSuccessChecker.process_item(ansible_item("foo", "bin/fuse")), True
        )

    def test_not_found(self):
        """Did not find eap home layers."""
        self.assertEqual(
            eap.ItemSuccessChecker.process_item(ansible_item("foo", "", rc=1)), False
        )


class TestProcessEapHomeLayersConf(unittest.TestCase):
    """Test looking for eap home layers conf."""

    def test_success(self):
        """Found eap home layers conf."""
        self.assertEqual(
            eap.ProcessEapHomeLayersConf.process(
                ansible_results([{"item": "foo", "stdout": "bin/fuse"}])
            ),
            {"foo": True},
        )

    def test_not_found(self):
        """Did not find eap home layers conf."""
        self.assertEqual(
            eap.ProcessEapHomeLayersConf.process(
                ansible_results([{"item": "foo", "stdout": "", "rc": 1}])
            ),
            {"foo": False},
        )


class TestProcessFindJbossEAPJarVer(unittest.TestCase):
    """Test ProcessFindJbossEAPJarVer."""

    def test_success_case(self):
        """Return stdout_lines in case of success."""
        in_line = (
            "1.3.6.Final-redhat-1**2018-01-18; "
            "1.3.6.Final-redhat-1**2018-01-18; "
            "1.3.6.Final-redhat-1**2018-01-18\n"
        )
        expected = {"version": "1.3.6.Final-redhat-1", "date": "2018-01-18"}
        self.assertEqual(
            eap.ProcessFindJbossEAPJarVer.process(ansible_result(in_line)),
            [expected, expected, expected],
        )


class TestProcessFindJbossEAPRunJarVer(unittest.TestCase):
    """Test ProcessFindJbossEAPRunJarVer."""

    def test_success_case(self):
        """Return stdout_lines in case of success."""
        in_line = (
            "1.3.6.Final-redhat-1**2018-01-18; "
            "1.3.6.Final-redhat-1**2018-01-18; "
            "1.3.6.Final-redhat-1**2018-01-18\n"
        )
        expected = {"version": "1.3.6.Final-redhat-1", "date": "2018-01-18"}
        self.assertEqual(
            eap.ProcessFindJbossEAPRunJarVer.process(ansible_result(in_line)),
            [expected, expected, expected],
        )
