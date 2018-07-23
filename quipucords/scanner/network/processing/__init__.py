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
from . import eap
from . import eap5
from . import brms
from . import fuse
from . import jws
from . import karaf
from . import cpu
from . import ifconfig
from . import date
from . import subman
from . import yum
from . import virt
