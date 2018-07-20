#!/usr/bin/env python
#
# Copyright (c) 2017-2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Constants for the Scan commands."""

SUBCOMMAND = 'scan'
ADD = 'add'
EDIT = 'edit'
START = 'start'
LIST = 'list'
JOB = 'job'
SHOW = 'show'
PAUSE = 'pause'
CANCEL = 'cancel'
RESTART = 'restart'
CLEAR = 'clear'

# Status values
SCAN_STATUS_CREATED = 'created'
SCAN_STATUS_PENDING = 'pending'
SCAN_STATUS_RUNNING = 'running'
SCAN_STATUS_PAUSED = 'paused'
SCAN_STATUS_CANCELED = 'canceled'
SCAN_STATUS_COMPLETED = 'completed'
SCAN_STATUS_FAILED = 'failed'


SCAN_URI = '/api/v1/scans/'
SCAN_JOB_URI = '/api/v1/jobs/'

SCAN_TYPE_CONNECT = 'connect'
SCAN_TYPE_INSPECT = 'inspect'

JBOSS_EAP = 'jboss_eap'
JBOSS_FUSE = 'jboss_fuse'
JBOSS_BRMS = 'jboss_brms'
JBOSS_WS = 'jboss_ws'
OPTIONAL_PRODUCTS = [JBOSS_EAP, JBOSS_FUSE, JBOSS_BRMS, JBOSS_WS]
