# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Utilities for processing Ansible task outputs."""

from scanner.network.processing import process


def get_line(lines, line_index=0):
    """Get a line from output.

    :param lines: list of output lines
    :param line_index: The index line to retrieve
    :returns: The specific line or empty string
    """
    num_lines = len(lines)
    if num_lines > line_index:
        return lines[line_index]
    return process.NO_DATA


# pylint: disable=too-few-public-methods
class InitLineFinder(process.Processor):
    """Process the output of an init system.

    For both chkconfig and systemctl list-unit-files, we look for
    lines where the first (whitespace-delineated) element contains
    keywords.
    """

    KEY = None
    KEYWORDS = None  # A list of keywords to search for

    @classmethod
    def process(cls, output):
        """Find lines where the first element contains a keyword."""
        matches = []

        for line in output['stdout_lines']:
            if not line:
                continue

            start = line.split()[0]
            # pylint: disable=not-an-iterable
            if any((keyword in start for keyword in cls.KEYWORDS)):
                matches.append(line.strip())

        return matches


class ProcessFindJarVer(process.Processor):
    """Process the results of a find jar version command."""

    KEY = None

    @staticmethod
    def process(output):
        """Return the command's output."""
        versions = []
        for line in output['stdout_lines']:
            if line == '':
                continue
            line_data = line.split('; ')
            for version_stamp in line_data:
                jar, date = version_stamp.split('**')
                version = {'jar': jar, 'date': date}
                versions.append(version)
        return versions
