# Copyright (c) 2022 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Helper function for specific assertions."""


def assert_elements_type(elements, expected_type):
    """Ensure all elements in a collection match expected type."""
    assert all(isinstance(el, expected_type) for el in elements), [
        type(p) for p in elements
    ]
