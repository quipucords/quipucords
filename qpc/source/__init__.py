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
"""Constants for the Sources commands."""

SUBCOMMAND = 'source'
ADD = 'add'
LIST = 'list'
EDIT = 'edit'
SHOW = 'show'
CLEAR = 'clear'

NETWORK_SOURCE_TYPE = 'network'
VCENTER_SOURCE_TYPE = 'vcenter'
SATELLITE_SOURCE_TYPE = 'satellite'

SOURCE_URI = '/api/v1/sources/'

BOOLEAN_CHOICES = ['True', 'False', 'true', 'false']
VALID_SSL_PROTOCOLS = ['SSLv23',
                       'TLSv1',
                       'TLSv1_1',
                       'TLSv1_2']
