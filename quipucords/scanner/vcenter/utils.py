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
"""Utilities used for VCenter operations."""

import atexit
from pyVim.connect import SmartConnectNoSSL, Disconnect
from api.vault import decrypt_data_as_unicode


def vcenter_connect(scan_task):
    """Connect to VCenter.

    :param scan_task: The scan task
    :returns: VCenter connection object.
    """
    credential = scan_task.source.credentials.all().first()
    user = credential.username
    host = scan_task.source.get_hosts()[0]
    password = decrypt_data_as_unicode(credential.password)
    port = scan_task.source.port

    # TO DO: Fix port handling and SSL options
    vcenter = SmartConnectNoSSL(host=host, user=user,
                                pwd=password, port=port)
    atexit.register(Disconnect, vcenter)

    return vcenter
