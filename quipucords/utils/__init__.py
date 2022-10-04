# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""
Common utils for quipucords.

All utils should be imported here so the internal api for importing is just
"from utils import some_util_func".
"""

from .deepget import deepget
from .default_getter import default_getter


def get_choice_ids(choices):
    """Retrieve choice ids."""
    return [choice[0] for choice in choices]
