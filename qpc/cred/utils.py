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
"""Utilities for the credential credentials module."""

from __future__ import print_function
import os
import sys
from getpass import getpass
from qpc.translation import _
import qpc.messages as messages


def validate_sshkeyfile(keyfile, parser):
    """Check if keyfile is present on the system exits if its not found.

    :param keyfile: the path to the keyfile
    :param parser: the cli parser to provide help information
    :returns: verified keyfile path
    """
    keyfile_path = os.path.abspath(os.path.normpath(keyfile))
    if not os.path.isfile(keyfile_path):
        print(_(messages.VALIDATE_SSHKEY % (keyfile)))
        parser.print_help()
        sys.exit(1)
    else:
        # set filename to the resolved keyfile_path
        return keyfile_path


def get_password(args, req_payload, add_none=True):
    """Collect the password value and place in credential dictionary.

    :param args: the command line arguments
    :param req_payload: the dictionary for the request
    :param add_none: add None for a key if True vs. not in dictionary
    :returns: the updated dictionary
    """
    if 'password' in args and args.password:
        print(_(messages.CONN_PASSWORD))
        pass_prompt = getpass()
        req_payload['password'] = pass_prompt or None
    elif add_none:
        req_payload['password'] = None
    if 'ssh_passphrase' in args and args.ssh_passphrase:
        print(_(messages.SSH_PASSPHRASE))
        pass_prompt = getpass()
        req_payload['ssh_passphrase'] = pass_prompt or None
    elif add_none:
        req_payload['ssh_passphrase'] = None
    if 'become_password' in args and args.become_password:
        print(_(messages.BECOME_PASSWORD))
        pass_prompt = getpass()
        req_payload['become_password'] = pass_prompt or None
    elif add_none:
        req_payload['become_password'] = None

    return req_payload


def build_credential_payload(args, cred_type, add_none=True):
    """Construct payload from command line arguments.

    :param args: the command line arguments
    :param add_none: add None for a key if True vs. not in dictionary
    :returns: the dictionary for the request payload
    """
    req_payload = {'name': args.name}
    if 'type' in args and cred_type is not None:
        req_payload['cred_type'] = cred_type
    if 'username' in args and args.username:
        req_payload['username'] = args.username
    if 'become_method' in args and args.become_method:
        req_payload['become_method'] = args.become_method
    if 'become_user' in args and args.become_user:
        req_payload['become_user'] = args.become_user
    if 'filename' in args and args.filename:
        req_payload['ssh_keyfile'] = args.filename
    elif add_none:
        req_payload['ssh_keyfile'] = None

    req_payload = get_password(args, req_payload, add_none)
    return req_payload
