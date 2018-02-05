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
"""Utilities for the source module."""

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


# pylint: disable=R0912
def build_source_payload(args, add_none=True):
    """Construct payload from command line arguments.

    :param args: the command line arguments
    :param add_none: add None for a key if True vs. not in dictionary
    :returns: the dictionary for the request payload
    """
    req_payload = {'name': args.name}
    options = None

    if hasattr(args, 'type') and args.type:
        req_payload['source_type'] = args.type

    if hasattr(args, 'hosts') and args.hosts:
        req_payload['hosts'] = args.hosts
    if hasattr(args, 'port') and args.port:
        req_payload['port'] = args.port
    elif add_none:
        req_payload['port'] = None
    if hasattr(args, 'credentials') and args.credentials:
        req_payload['credentials'] = args.credentials
    elif add_none:
        req_payload['credentials'] = None
    if hasattr(args, 'satellite_version') and args.satellite_version:
        if options is None:
            options = {'satellite_version': args.satellite_version}
        else:
            options['satellite_version'] = args.satellite_version
    if (hasattr(args, 'ssl_cert_verify') and
            args.ssl_cert_verify is not None):
        ssl_cert_verify = args.ssl_cert_verify == 'True'
        if options is None:
            options = {'ssl_cert_verify': ssl_cert_verify}
        else:
            options['ssl_cert_verify'] = ssl_cert_verify

    if options is not None:
        req_payload['options'] = options

    return req_payload
