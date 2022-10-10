# Copyright (C) 2022  Red Hat, Inc.

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.

"""get_from_object_or_dict module."""


def get_from_object_or_dict(instance, dict_obj, key):
    """Get an attribute from instance or key from dictionary - in this order."""
    return getattr(instance, key, None) or dict_obj.get(key)
