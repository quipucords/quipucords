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
"""Describes the reusable filters."""

from django_filters.rest_framework import Filter


class ListFilter(Filter):
    """Add query filter capability to provide a list of filter values."""

    def filter(self, qs, value):
        """Filter based on query string and value."""
        if not value:
            return qs

        # For django-filter versions < 0.13,
        # use lookup_type instead of lookup_expr
        self.lookup_expr = "in"
        values = value.split(",")

        # pylint: disable=super-with-arguments
        return super(ListFilter, self).filter(qs, values)
