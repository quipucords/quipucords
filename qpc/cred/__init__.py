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
"""Constants for the Credential commands."""

SUBCOMMAND = 'cred'
ADD = 'add'
LIST = 'list'
EDIT = 'edit'
SHOW = 'show'
CLEAR = 'clear'


NETWORK_CRED_TYPE = 'network'
VCENTER_CRED_TYPE = 'vcenter'
SATELLITE_CRED_TYPE = 'satellite'

BECOME_SUDO = 'sudo'
BECOME_SU = 'su'
BECOME_PBRUN = 'pbrun'
BECOME_PFEXEC = 'pfexec'
BECOME_DOAS = 'doas'
BECOME_DZDO = 'dzdo'
BECOME_KSU = 'ksu'
BECOME_RUNAS = 'runas'

BECOME_CHOICES = [BECOME_SUDO,
                  BECOME_SU,
                  BECOME_PBRUN,
                  BECOME_PFEXEC,
                  BECOME_DOAS,
                  BECOME_DZDO,
                  BECOME_KSU,
                  BECOME_RUNAS]

CREDENTIAL_URI = '/api/v1/credentials/'
