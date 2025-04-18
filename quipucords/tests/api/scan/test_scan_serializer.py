"""Test special methods of the ScanSerializer class."""

import pytest
from rest_framework.exceptions import ValidationError

from api.scan.serializer import ScanSerializer


@pytest.mark.parametrize("search_directories", [None, [], ["/a"], ["/a", "/b"]])
def test_validate_search_directories_with_acceptable_inputs(search_directories):
    """Tests the get_extra_vars with search_directories with acceptable values."""
    result = ScanSerializer.validate_search_directories(search_directories)
    assert result == search_directories  # yes, output==input means success here.


@pytest.mark.parametrize(
    "search_directories",
    [
        "/a",  # is not a list
        [1],  # is not a list of strings
        ["a"],  # is not a list of absolute path like strings
    ],
)
def test_validate_search_directories_with_bad_inputs(search_directories):
    """Tests the get_extra_vars with search_directories contains bad values."""
    with pytest.raises(ValidationError):
        ScanSerializer.validate_search_directories(search_directories)
