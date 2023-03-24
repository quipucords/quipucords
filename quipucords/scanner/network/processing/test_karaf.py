"""Unit tests for initial processing."""

# pylint: disable=missing-docstring

import unittest

from scanner.network.processing import karaf, process
from scanner.network.processing.util_for_test import ansible_result, ansible_results


class TestProcessKarafRunningProcesses(unittest.TestCase):
    """Test ProcessKarafRunningPaths."""

    def test_success_case(self):
        """Strip spaces from good input."""
        assert (
            karaf.ProcessKarafRunningProcesses.process(ansible_result(" good "))
            == "good"
        )

    def test_find_warning(self):
        """Fail if we get the special find warning string."""
        assert (
            karaf.ProcessKarafRunningProcesses.process(
                ansible_result(karaf.FIND_WARNING)
            )
            == process.NO_DATA
        )


class TestProcessFindKaraf(unittest.TestCase):
    """Test ProcessFindJKaraf."""

    def test_success_case(self):
        """Return stdout_lines in case of success."""
        assert karaf.ProcessFindKaraf.process(ansible_result("a\nb\nc")) == [
            "a",
            "b",
            "c",
        ]


class TestProcessLocateKaraf(unittest.TestCase):
    """Test using locate to find karaf.jar."""

    def test_success(self):
        """Found karaf.jar."""
        assert karaf.ProcessLocateKaraf.process(ansible_result("a\nb\nc")) == [
            "a",
            "b",
            "c",
        ]

    def test_not_found(self):
        """Did not find karaf.jar."""
        assert karaf.ProcessLocateKaraf.process(ansible_result("")) == []


class TestProcessKarafInitFiles(unittest.TestCase):
    """Test looking for 'jboss' or 'fuse' init files."""

    processors = [karaf.ProcessJbossFuseChkconfig, karaf.ProcessJbossFuseSystemctl]

    def test_no_fuse(self):
        """No 'fuse' found."""
        for processor in self.processors:
            # Blank line in input to check that processor will skip it.
            assert processor.process(ansible_result("foo\nbar\n\nbaz")) == []

    def test_fuse_skipped(self):
        """'fuse' not found for Systemctl."""
        for processor in self.processors:
            expected = ["sys-fs-fuse-connections.mount"]
            if processor.IGNORE_WORDS is not None:
                expected = []

            assert (
                processor.process(
                    ansible_result("  foo\n  sys-fs-fuse-connections.mount\n  baz fuse")
                )
                == expected
            )

    def test_fuse(self):
        """'fuse' found."""
        for processor in self.processors:
            assert processor.process(
                ansible_result("  foo\n  fuse bar\n  baz fuse")
            ) == ["fuse bar"]


class TestProcessKarafHomeBinFuse(unittest.TestCase):
    """Test using locate to find karaf home bin fuse."""

    def test_success(self):
        """Found karaf.jar."""
        assert karaf.ProcessKarafHomeBinFuse.process(
            ansible_results([{"item": "foo", "stdout": "bin/fuse"}])
        ) == {"foo": True}

    def test_not_found(self):
        """Did not find karaf home bin fuse."""
        assert karaf.ProcessKarafHomeBinFuse.process(
            ansible_results([{"item": "foo", "stdout": "", "rc": 1}])
        ) == {"foo": False}


class TestProcessKarafHomeSystemOrgJboss(unittest.TestCase):
    """Test using locate to find karaf home bin fuse."""

    def test_success(self):
        """Found karaf.jar."""
        assert karaf.ProcessKarafHomeSystemOrgJboss.process(
            ansible_results([{"item": "foo", "stdout": "bar"}])
        ) == {str(["bar"]): True}

    def test_not_found(self):
        """Did not find karaf home bin fuse."""
        assert karaf.ProcessKarafHomeSystemOrgJboss.process(
            ansible_results([{"item": "foo", "stdout": "", "rc": 1}])
        ) == {"[]": False}


class TestProcessJbossFuseCamelVersion(unittest.TestCase):
    """Test the output of looking for camel version."""

    def test_success(self):
        """Found camel-core."""
        assert karaf.ProcessJbossFuseCamelVersion.process(
            ansible_results([{"item": "/fake/dir", "stdout": "redhat-630187"}])
        ) == [{"install_home": "/fake/dir", "version": ["redhat-630187"]}]

    def test_not_found(self):
        """Did not find camel-core."""
        assert (
            karaf.ProcessJbossFuseCamelVersion.process(
                ansible_results([{"item": "foo", "stdout": "", "rc": 1}])
            )
            == []
        )

    def on_eap_test_success(self):
        """Found camel on eap home dir."""
        assert karaf.ProcessJbossFuseOnEapCamelVersion.process(
            ansible_results([{"item": "/fake/dir", "stdout": "redhat-630187"}])
        ) == [{"install_home": "/fake/dir", "version": ["redhat-630187"]}]

    def on_eap_test_not_found(self):
        """Did not find camel on eap home dir."""
        assert (
            karaf.ProcessJbossFuseOnEapCamelVersion.process(
                ansible_results([{"item": "foo", "stdout": "", "rc": 1}])
            )
            == []
        )

    def locate_test_success(self):
        """Found camel with locate."""
        assert karaf.ProcessLocateCamel.process(
            ansible_results([{"item": "/fake/dir", "stdout_lines": "redhat-630187"}])
        ) == list(set("redhat-630187"))

    def locate_test_not_found(self):
        """Did not find camel with locate."""
        assert (
            karaf.ProcessLocateCamel.process(
                ansible_results([{"item": "foo", "stdout": "", "rc": 1}])
            )
            == []
        )


class TestProcessJbossFuseActivemqVersion(unittest.TestCase):
    """Test the output of looking for activemq version."""

    def test_success(self):
        """Found activemq."""
        assert karaf.ProcessJbossFuseActivemqVersion.process(
            ansible_results([{"item": "/fake/dir", "stdout": "redhat-630187"}])
        ) == [{"install_home": "/fake/dir", "version": ["redhat-630187"]}]

    def test_not_found(self):
        """Did not find activemq."""
        assert (
            karaf.ProcessJbossFuseActivemqVersion.process(
                ansible_results([{"item": "foo", "stdout": "", "rc": 1}])
            )
            == []
        )

    def on_eap_test_success(self):
        """Found activemq on eap home dir."""
        assert karaf.ProcessJbossFuseOnEapActivemqVersion.process(
            ansible_results([{"item": "/fake/dir", "stdout": "redhat-630187"}])
        ) == [{"install_home": "/fake/dir", "version": ["redhat-630187"]}]

    def on_eap_test_not_found(self):
        """Did not find activemq on eap home dir."""
        assert (
            karaf.ProcessJbossFuseOnEapActivemqVersion.process(
                ansible_results([{"item": "foo", "stdout": "", "rc": 1}])
            )
            == []
        )

    def locate_test_success(self):
        """Found activemq with locate."""
        assert karaf.ProcessLocateActivemq.process(
            ansible_results([{"item": "/fake/dir", "stdout_lines": "redhat-630187"}])
        ) == list(set("redhat-630187"))

    def locate_test_not_found(self):
        """Did not find activemq with locate."""
        assert (
            karaf.ProcessLocateActivemq.process(
                ansible_results([{"item": "foo", "stdout": "", "rc": 1}])
            )
            == []
        )


class TestProcessJbossFuseCxfVersion(unittest.TestCase):
    """Test the output of looking for cxf version."""

    def test_success(self):
        """Found cxf."""
        assert karaf.ProcessJbossFuseCxfVersion.process(
            ansible_results([{"item": "/fake/dir", "stdout": "redhat-630187"}])
        ) == [{"install_home": "/fake/dir", "version": ["redhat-630187"]}]

    def test_not_found(self):
        """Did not find cxf."""
        assert (
            karaf.ProcessJbossFuseCxfVersion.process(
                ansible_results([{"item": "foo", "stdout": "", "rc": 1}])
            )
            == []
        )

    def on_eap_test_success(self):
        """Found cxf on eap home dir."""
        assert karaf.ProcessJbossFuseOnEapCxfVersion.process(
            ansible_results([{"item": "/fake/dir", "stdout": "redhat-630187"}])
        ) == [{"install_home": "/fake/dir", "version": ["redhat-630187"]}]

    def on_eap_test_not_found(self):
        """Did not find cxf on eap home dir."""
        assert (
            karaf.ProcessJbossFuseOnEapCxfVersion.process(
                ansible_results([{"item": "foo", "stdout": "", "rc": 1}])
            )
            == []
        )

    def locate_test_success(self):
        """Found cxf with locate."""
        assert karaf.ProcessLocateCxf.process(
            ansible_results([{"item": "/fake/dir", "stdout_lines": "redhat-630187"}])
        ) == list(set("redhat-630187"))

    def locate_test_not_found(self):
        """Did not find cxf with locate."""
        assert (
            karaf.ProcessLocateCxf.process(
                ansible_results([{"item": "foo", "stdout": "", "rc": 1}])
            )
            == []
        )
