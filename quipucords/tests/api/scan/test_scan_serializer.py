"""Test special methods of the ScanSerializer class."""

import pytest
from rest_framework.exceptions import ValidationError

from api.scan.serializer import ScanSerializer


def test_get_extra_vars_missing_search_directories_empty():
    """Tests the get_extra_vars with search_directories empty."""
    search_directories = []
    ScanSerializer.validate_search_directories(search_directories)


def test_get_extra_vars_missing_search_directories_w_int():
    """Tests the get_extra_vars with search_directories contains int."""
    with pytest.raises(ValidationError):
        ScanSerializer.validate_search_directories([1])


def test_get_extra_vars_missing_search_directories_w_not_path():
    """Tests the get_extra_vars with search_directories no path."""
    with pytest.raises(ValidationError):
        ScanSerializer.validate_search_directories(["a"])


def test_get_extra_vars_missing_search_directories_w_path():
    """Tests the get_extra_vars with search_directories no path."""
    ScanSerializer.validate_search_directories(["/a"])
