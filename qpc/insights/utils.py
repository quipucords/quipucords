#!/usr/bin/env python
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
"""Utilities for the insights module."""

from __future__ import print_function


def check_insights_install(streamdata):
    """Will check stream data for failure clause."""
    failures = ['FAILURE',
                'command not found',
                'No module named \'insights\'']
    for fail in failures:
        if fail in str(streamdata):
            return False
    return True


def check_successful_upload(streamdata):
    """Will check stream data for success clause."""
    success = 'Successfully uploaded report'
    if success in str(streamdata):
        return True
    return False


def test_insights_command(tar_name, content_type):
    """Will create the insights command for testing locally."""
    return ['sudo',
            'EGG=/etc/insights-client/rpm.egg',
            'BYPASS_GPG=True',
            'insights-client',
            '--no-gpg',
            '--payload=' + tar_name,
            content_type]


def insights_command(tar_name, content_type):
    """Will create the insights command."""
    return ['sudo',
            'insights-client',
            '--payload=' + tar_name,
            content_type]
