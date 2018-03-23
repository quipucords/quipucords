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


class FindJarVer(process.Processor):
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
                version = {'version': jar, 'date': date}
                versions.append(version)
        return versions


class FindJar(process.Processor):
    """Process the results of a find jar command."""

    KEY = None

    @staticmethod
    def process(output):
        """Return the command's output."""
        versions = []
        for line in output['stdout_lines']:
            if line == '':
                continue
            line_data = line.split('; ')
            versions += line_data
        return versions


class IndicatorFileFinder(process.Processor):
    """Look for indicator files in the output of many 'ls -1's.

    Use by subclassing and defining a class variable INDICATOR_FILES,
    which is an iterable of the files to look for. Example usage:

    class ProcessMyLsResults(IndicatorFileFinder):
        KEY = 'my_great_ls'
        INDICATOR_FILES = ['find', 'my', 'directory']
    """

    KEY = None

    @classmethod
    def process(cls, output):
        """Find indicator files in the output, item by item."""
        results = {}

        for item in output['results']:
            directory = item['item']
            if item['rc']:
                results[directory] = []
                continue

            files = item['stdout_lines']
            # pylint: disable=no-member
            found_in_dir = [filename for filename in cls.INDICATOR_FILES
                            if filename in files]
            if found_in_dir:
                results[directory] = found_in_dir
            else:
                results[directory] = []

        return results


class StdoutSearchProcessor(process.Processor):
    """Look for a string in the output of a with_items task.

    Use by subclassing and setting SEARCH_STRING to the string to look
    for.
    """

    KEY = None
    SEARCH_STRING = None

    @classmethod
    def process(cls, output):
        """Process the output of a with_items task from Ansible.

        :param output: the output of a with_items task.

        :returns: a dictionary mapping each item name to True if
          SEARCH_STRING was found in that item's stdout, and False
          otherwise.
        """
        results = {}
        for item in output['results']:
            item_name = item['item']
            if item['rc']:
                results[item_name] = False
            else:
                results[item_name] = cls.SEARCH_STRING in item['stdout']

        return results


class StdoutPassthroughProcessor(process.Processor):
    """Pass through stdout to the fingerprinter, or False on error.

    Used for the output of 'cat some-file', where some-file might not
    exist. Works for with-items tasks.
    """

    KEY = None

    @staticmethod
    def process(output):
        """Process the output of a with_items task from Ansible.

        :param output: the output of a with_items task.

        :returns: a dictionary mapping each item name to the item's
        stdout if the item's 'rc' is zero, or False otherwise.
        """
        return {item['item']: item['stdout'] if item['rc'] == 0 else False
                for item in output['results']}
