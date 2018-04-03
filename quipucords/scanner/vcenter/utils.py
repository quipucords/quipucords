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
"""Utilities used for VCenter operations."""
import atexit
import ssl

from api.vault import decrypt_data_as_unicode

from pyVim.connect import Disconnect, SmartConnect, SmartConnectNoSSL


def vcenter_connect(scan_task):
    """Connect to VCenter.

    :param scan_task: The scan task
    :returns: VCenter connection object.
    """
    vcenter = None
    disable_ssl = None
    ssl_cert_verify = None
    ssl_protocol = None
    source = scan_task.source
    credential = source.credentials.all().first()
    user = credential.username
    host = scan_task.source.get_hosts()[0]
    password = decrypt_data_as_unicode(credential.password)
    port = scan_task.source.port
    options = source.options

    if options:
        if options.disable_ssl and options.disable_ssl is True:
            disable_ssl = True
        if options.ssl_cert_verify is not None:
            ssl_cert_verify = options.ssl_cert_verify
        ssl_protocol = options.get_ssl_protocol()

    if disable_ssl:
        vcenter = SmartConnectNoSSL(host=host, user=user,
                                    pwd=password, port=port)
    elif ssl_protocol is None and ssl_cert_verify is None:
        vcenter = SmartConnect(host=host, user=user,
                               pwd=password, port=port)
    else:
        ssl_context = None
        if ssl_protocol is None:
            ssl_context = ssl.SSLContext(protocol=ssl.PROTOCOL_SSLv23)
        else:
            ssl_context = ssl.SSLContext(protocol=ssl_protocol)
        if ssl_cert_verify is False:
            ssl_context.verify_mode = ssl.CERT_NONE
        vcenter = SmartConnect(host=host, user=user,
                               pwd=password, port=port,
                               sslContext=ssl_context)

    atexit.register(Disconnect, vcenter)

    return vcenter
