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

from scanner.network.processing import fuse
from scanner.network.processing.util_for_test import ansible_result


class TestProcessFindJbossActiveMQJar(unittest.TestCase):
    """Test ProcessFindJbossActiveMQJar."""

    def test_success_case(self):
        """Return stdout_lines in case of success."""
        in_line = "redhat-620133; redhat-630187\n"
        self.assertEqual(
            fuse.ProcessFindJbossActiveMQJar.process(ansible_result(in_line)),
            ["redhat-620133", "redhat-630187"],
        )


class TestProcessFindJbossCamelJar(unittest.TestCase):
    """Test ProcessFindJbossCamelJar."""

    def test_success_case(self):
        """Return stdout_lines in case of success."""
        in_line = "redhat-620133; redhat-630187\n"
        self.assertEqual(
            fuse.ProcessFindJbossCamelJar.process(ansible_result(in_line)),
            ["redhat-620133", "redhat-630187"],
        )


class TestProcessFindJbossCXFJar(unittest.TestCase):
    """Test ProcessFindJbossCXFJar."""

    def test_success_case(self):
        """Return stdout_lines in case of success."""
        in_line = "redhat-620133; redhat-630187\n"
        self.assertEqual(
            fuse.ProcessFindJbossCXFJar.process(ansible_result(in_line)),
            ["redhat-620133", "redhat-630187"],
        )
