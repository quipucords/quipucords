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
"""Constants for the server configuration commands."""

SUBCOMMAND = 'server'
CONFIG = 'config'
LOGIN = 'login'
LOGOUT = 'logout'
STATUS = 'status'

LOGIN_URI = '/api/v1/token/'
LOGOUT_URI = '/api/v1/users/logout/'
STATUS_URI = '/api/v1/status/'
