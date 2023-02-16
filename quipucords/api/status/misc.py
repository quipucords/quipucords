# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""Status misc module."""

from functools import lru_cache

from .model import ServerInformation


@lru_cache
def get_server_id():
    """Get server_id and cache it."""
    return ServerInformation.create_or_retrieve_server_id()
