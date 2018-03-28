# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Initial processing of the shell output from the jboss_brms role."""

import logging
import pathlib
import posixpath
import re
from scanner.network.processing import process

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# pylint: disable=too-few-public-methods

# #### Processors ####

# All of the processors in this file (except for
# ProcessFindBRMSKieWarVer; see its comment) return lists of
# (directory, version_string) tuples. A version_string is a string
# that comes from the Ansible task results and that can be mapped to a
# BRMS version in the fingerprinter. The directory is the base
# directory associated with this particular version string. Keeping
# the base directory around makes the results more transparent to
# users, by giving them a place to go look to see the installation we
# found. It also lets us report the situation where there are multiple
# BRMS installs with the same version on the same host.

# The (directory, version_string) lists are guaranteed to have unique
# elements. Logically they are sets, not lists, but we need to be able
# to JSON serialize them, so we build them as sets and then convert to
# lists just before returning.


def normalize_path(path):
    """Normalize a path.

    We need to normalize all of the directories we return so that they
    will be deduplicated by Python's set class.
    """
    return pathlib.PurePath(path).as_posix()


IMPLEMENTATION_VERSION_RE = re.compile(r'Implementation-Version:\s*(.*)\s*')


class ProcessJbossBRMSManifestMF(process.Processor):
    """Get the Implementation-Version from a MANIFEST.MF file."""

    KEY = 'jboss_brms_manifest_mf'

    @staticmethod
    def process_item(item):
        """Get the implementation version from a MANIFEST.MF file."""
        if item['rc']:
            return None

        directory = normalize_path(item['item'])
        for line in item['stdout_lines']:
            match = IMPLEMENTATION_VERSION_RE.match(line)
            if match:
                return (normalize_path(directory), match.group(1))

        return None

    @staticmethod
    def process(output):
        """Return a set of (directory, version string) pairs."""
        results = set()
        for item in output['results']:
            val = ProcessJbossBRMSManifestMF.process_item(item)
            if val:
                results.add(val)

        return list(results)


def enclosing_war_archive(path):
    """Find the BRMS war archive containing path.

    :param path: a filesystem path

    :returns: the path to the nearest BRMS war archive enclosing path,
        or None if not in a war archive.
    """
    parts = pathlib.PurePath(path).parts

    for i in range(len(parts) - 1, -1, -1):
        if parts[i].startswith('kie-server') or \
           parts[i].startswith('business-central'):
            return pathlib.PurePath(*parts[:i + 1]).as_posix()


KIE_FILENAME_RE = re.compile(r'kie-api-(.*)\.jar.*')


class ProcessJbossBRMSKieBusinessCentral(process.Processor):
    """Return filenames and their enclosing BRMS war archive."""

    KEY = 'jboss_brms_kie_in_business_central'

    @staticmethod
    def process(output):
        """Return a list of (base war archive, version string) pairs."""
        results = set()
        for item in output['results']:
            if item['rc']:
                continue

            directory = normalize_path(item['item'])
            for line in item['stdout_lines']:
                filename = posixpath.basename(line)
                match = KIE_FILENAME_RE.match(filename)
                if not match:
                    continue
                results.add((directory, match.group(1)))

        return list(results)


class ProcessLocateKieApiFiles(process.Processor):
    """Process locate results for kie-api files."""

    KEY = 'jboss_brms_locate_kie_api'
    DEPS = ['have_locate']

    @staticmethod
    def process(output):
        """Return a list of (base war archive, version string) pairs."""
        results = set()
        for line in output['stdout_lines']:
            filename = posixpath.basename(line)
            directory = enclosing_war_archive(line)
            match = KIE_FILENAME_RE.match(filename)
            if not match:
                continue
            results.add((directory, match.group(1)))

        return list(results)


class JarNameProcessor(process.Processor):
    """Process the results of a find command."""

    KEY = None

    @staticmethod
    def process(output):
        """Split lines into directory / filename pairs."""
        results = set()

        for line in output['stdout_lines']:
            directory, filename = posixpath.split(line)
            if not directory or not filename:
                continue
            results.add((normalize_path(directory), filename))

        return list(results)


class ProcessFindBRMSKieApiVer(JarNameProcessor):
    """Process a list of kie-api* files."""

    KEY = 'jboss_brms_kie_api_ver'


class ProcessFindBRMSDroolsCoreVer(JarNameProcessor):
    """Process the results of a find command."""

    KEY = 'jboss_brms_drools_core_ver'


class ProcessFindBRMSKieWarVer(process.Processor):
    """Process the results of a find command."""

    # This class can't return a list of (directory, version_string)
    # pairs like the rest because its task processes compressed war
    # archives, and we don't have a test case for those. I don't want
    # to mess with the output until I have a way to verify that the
    # changes work, so just pass this through for now.

    KEY = 'jboss_brms_kie_war_ver'

    @staticmethod
    def process(output):
        """Return the command's output."""
        return output['stdout_lines']
