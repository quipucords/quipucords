#!/usr/bin/env python
#
# Copyright (c) 2017 Red Hat, Inc.
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
START = 'start'
LIST = 'list'
SHOW = 'show'
PAUSE = 'pause'
CANCEL = 'cancel'
RESTART = 'restart'

# Status values
SCAN_STATUS_CREATED = 'created'
SCAN_STATUS_PENDING = 'pending'
SCAN_STATUS_RUNNING = 'running'
SCAN_STATUS_PAUSED = 'paused'
SCAN_STATUS_CANCELED = 'canceled'
SCAN_STATUS_COMPLETED = 'completed'
SCAN_STATUS_FAILED = 'failed'


SCAN_URI = '/api/v1/scans/'

SCAN_TYPE_CONNECT = 'connect'
SCAN_TYPE_INSPECT = 'inspect'

# Scan Options
SCAN_JBOSS_EAP = 'jboss-eap'
SCAN_JBOSS_FUSE = 'jboss-fuse'
SCAN_JBOSS_BRMS = 'jboss-brms'
# SCAN_EAP_FUSE = [SCAN_JBOSS_EAP, SCAN_JBOSS_FUSE]
# SCAN_EAP_BRMS = 'jboss-eap','jboss-brms'
#SCAN_EAP_FUSE_BRMS = ['jboss-eap', 'jboss-fuse', 'jboss-brms']

SCAN_OPTIONS = [SCAN_JBOSS_EAP,
                SCAN_JBOSS_FUSE,
                SCAN_JBOSS_BRMS]
                # SCAN_EAP_FUSE,
                # SCAN_EAP_BRMS,
                # SCAN_EAP_FUSE_BRMS]
