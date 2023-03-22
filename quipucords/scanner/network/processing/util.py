"""Utilities for processing Ansible task outputs."""

import logging

from scanner.network.processing import process

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


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


class InitLineFinder(process.Processor):
    """Process the output of an init system.

    For both chkconfig and systemctl list-unit-files, we look for
    lines where the first (whitespace-delineated) element contains
    keywords.
    """

    KEY = None
    KEYWORDS = None  # A list of keywords to search for
    IGNORE_WORDS = None  # A list of words to ignore

    @classmethod
    def process(cls, output, dependencies=None):
        """Find lines where the first element contains a keyword."""
        matches = []

        for line in output["stdout_lines"]:
            if not line:
                continue

            start = line.split()[0]
            # pylint: disable=not-an-iterable
            if any((keyword in start for keyword in cls.KEYWORDS)):
                if cls.IGNORE_WORDS and not any(
                    (ignore in start for ignore in cls.IGNORE_WORDS)
                ):
                    matches.append(line.strip())
                elif cls.IGNORE_WORDS is None:
                    matches.append(line.strip())

        return matches


class FindJarVer(process.Processor):
    """Process the results of a find jar version command."""

    KEY = None

    @staticmethod
    def process(output, dependencies=None):
        """Return the command's output."""
        versions = []
        for line in output["stdout_lines"]:
            if line == "":
                continue
            line_data = line.split("; ")
            for version_stamp in line_data:
                jar, date = version_stamp.split("**")
                version = {"version": jar, "date": date}
                versions.append(version)
        return versions


class FindJar(process.Processor):
    """Process the results of a find jar command."""

    KEY = None

    @staticmethod
    def process(output, dependencies=None):
        """Return the command's output."""
        versions = []
        for line in output["stdout_lines"]:
            if line.strip() == "":
                continue
            line_data = line.split("; ")
            versions += line_data
        return versions


class PerItemProcessor(process.Processor):
    """Process the output of an Ansible with-items task.

    Calls cls.processItem() on each item of the result and returns a
    dict mapping item name to process_item output. If process_item
    returns None for an item or raises an exception, that item will
    not be in the result dictionary.

    The big benefit of this class is that it simplifies testing for
    its subclasses, because they only need to check that their
    process_item method works.
    """

    KEY = None

    @classmethod
    def process(cls, output, dependencies=None):
        """Process the output of an Ansible with-items task."""
        result = {}
        for item in output["results"]:
            item_name = item["item"]
            if item_name:
                try:
                    val = cls.process_item(item)
                except Exception as ex:  # pylint: disable=broad-except
                    logger.debug("Processor for %s hit error on %s", cls.KEY, item)
                    logger.exception(ex)
                    val = None
                if val is not None:
                    result[item_name] = val

        return result

    @staticmethod
    def process_item(item):
        """Override this method to provide per-item processing."""
        raise NotImplementedError()


class IndicatorFileFinder(PerItemProcessor):
    """Look for indicator files in the output of many 'ls -1's.

    Use by subclassing and defining a class variable INDICATOR_FILES,
    which is an iterable of the files to look for. Example usage:

    class ProcessMyLsResults(IndicatorFileFinder):
        KEY = 'my_great_ls'
        INDICATOR_FILES = ['find', 'my', 'directory']
    """

    KEY = None

    @classmethod
    def process_item(cls, item):
        """Look for indicator files in item's stdout lines."""
        if item.get("rc", True):
            return []

        files = item["stdout_lines"]
        # pylint: disable=no-member
        found_in_dir = [
            filename for filename in cls.INDICATOR_FILES if filename in files
        ]
        if found_in_dir:
            return found_in_dir

        return []


class StdoutSearchProcessor(PerItemProcessor):
    """Look for a string in the output of a with_items task.

    Use by subclassing and setting SEARCH_STRING to the string to look
    for.
    """

    KEY = None
    SEARCH_STRING = None

    @classmethod
    def process_item(cls, item):
        """Search stdout for the SEARCH_STRING."""
        if item.get("rc", True):
            return False

        return cls.SEARCH_STRING in item["stdout"]


class StdoutPassthroughProcessor(PerItemProcessor):
    """Pass through stdout to the fingerprinter, or False on error.

    Used for the output of 'cat some-file', where some-file might not
    exist.
    """

    KEY = None

    @staticmethod
    def process_item(item):
        """Make sure item succeeded and pass stdout through."""
        return item["rc"] == 0 and item["stdout"].strip()
