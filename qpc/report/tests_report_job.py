#
# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test the CLI module."""

import os
import sys
import time
import unittest
from argparse import ArgumentParser, Namespace
from io import StringIO

import qpc.messages as messages
from qpc.tests_utilities import DEFAULT_CONFIG, HushUpStderr, redirect_stdout
from qpc.utils import get_server_location, write_server_config

import requests_mock

PARSER = ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='subcommand')


class ReportJobTests(unittest.TestCase):
    """Class for testing the job commands for qpc."""

    # pylint: disable=invalid-name
    def setUp(self):
        """Create test setup."""
        pass

    def tearDown(self):
        """Remove test setup."""
        pass

    def test_job_valid_id(self):
        """Test the job command with a vaild ID"""
        pass

    def test_job_id_not_exist(self):
        """Test the job command with an invalid ID"""
        pass
