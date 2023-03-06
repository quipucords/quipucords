"""Common pagination class."""

from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """Create standard paginiation class with page size."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 1000
