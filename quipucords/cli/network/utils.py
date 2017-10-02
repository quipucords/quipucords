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
""" Utilities for the network profile module"""

from __future__ import print_function
from argparse import ArgumentTypeError


def validate_port(arg):
    """Check that arg is a valid port.

    :param arg: either a string or an integer.
    :returns: The arg, as an integer.
    :raises: ValueError, if arg is not a valid port.
    """

    if isinstance(arg, str):
        try:
            arg = int(arg)
        except ValueError:
            raise ArgumentTypeError('Port value %s'
                                    ' should be a positive integer'
                                    ' in the valid range (0-65535)' % arg)
    elif not isinstance(arg, int):
        raise ArgumentTypeError('Port value %s should be a positive integer'
                                ' in the valid range (0-65535)' % arg)

    # We need to support both system and user ports (see
    # https://en.wikipedia.org/wiki/Registered_port) because we don't
    # know how the user will have configured their system.
    if arg < 0 or arg > 65535:
        raise ArgumentTypeError('Port value %s should be a positive integer'
                                ' in the valid range (0-65535)' % arg)

    return arg


def build_profile_payload(args, add_none=True):
    """Construct payload from command line arguments

    :param args: the command line arguments
    :param add_none: add None for a key if True vs. not in dictionary
    :returns: the dictionary for the request payload
    """
    req_payload = {'name': args.name}
    if hasattr(args, 'hosts') and args.hosts:
        req_payload['hosts'] = args.hosts
    elif add_none:
        req_payload['hosts'] = None
    if hasattr(args, 'ssh_port') and args.ssh_port:
        req_payload['ssh_port'] = args.ssh_port
    elif add_none:
        req_payload['ssh_port'] = None
    if hasattr(args, 'credentials') and args.credentials:
        req_payload['credentials'] = args.credentials
    elif add_none:
        req_payload['credentials'] = None

    return req_payload
