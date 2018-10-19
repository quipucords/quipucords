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
"""Constants for the Report commands."""

SUBCOMMAND = 'report'

DEPLOYMENTS = 'deployments'
DETAILS = 'details'
MERGE = 'merge'
MERGE_STATUS = 'merge-status'

# deprecated
SUMMARY = 'summary'
DETAIL = 'detail'

REPORT_URI = '/api/v1/reports/'
DETAILS_PATH_SUFFIX = '/details/'
DEPLOYMENTS_PATH_SUFFIX = '/deployments/'
ASYNC_MERGE_URI = '/api/v1/reports/merge/jobs/'
