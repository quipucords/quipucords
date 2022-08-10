# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Initial processing for facts coming from Ansible."""

# flake8: noqa
from . import (
    brms,
    cloud_provider,
    cpu,
    date,
    dmi,
    eap,
    eap5,
    fuse,
    ifconfig,
    jws,
    karaf,
    redhat_packages,
    subman,
    system_purpose,
    user_data,
    virt,
    yum,
)
