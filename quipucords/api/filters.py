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
