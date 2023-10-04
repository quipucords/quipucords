"""Test the common util."""

import io
import json
import tarfile
from collections import OrderedDict

import pytest

from api.common.common_report import CSVHelper, create_tar_buffer, encode_content
from tests.report_utils import extract_files_from_tarball


@pytest.fixture
def csv_helper():
    """Create a CSVHelper."""
    return CSVHelper()


def test_csv_serialize_empty_values(csv_helper):
    """Test csv helper with empty values."""
    # Test Empty case
    value = csv_helper.serialize_value("header", {})
    assert value == ""
    value = csv_helper.serialize_value("header", [])
    assert value == ""


def test_csv_serialize_dict_1_key(csv_helper):
    """Test csv helper with 1 key dict."""
    test_python = {"key": "value"}
    value = csv_helper.serialize_value("header", test_python)
    assert value == "{key:value}"


def test_csv_serialize_list_1_value(csv_helper):
    """Test csv helper with 1 item list."""
    test_python = ["value"]
    value = csv_helper.serialize_value("header", test_python)
    assert value == "[value]"


def test_csv_serialize_dict_2_keys(csv_helper):
    """Test csv helper with 2 key dict."""
    # Test flat with 2 entries
    test_python = OrderedDict()
    test_python["key1"] = "value1"
    test_python["key2"] = "value2"
    value = csv_helper.serialize_value("header", test_python)
    assert value == "{key1:value1;key2:value2}"


def test_csv_serialize_list_2_values(csv_helper):
    """Test csv helper with 2 item list."""
    test_python = ["value1", "value2"]
    value = csv_helper.serialize_value("header", test_python)
    assert value == "[value1;value2]"


def test_csv_serialize_dict_nested(csv_helper):
    """Test csv helper with dict containing nested list/dict."""
    test_python = OrderedDict()
    test_python["key"] = "value"
    test_python["dict"] = {"nkey": "nvalue"}
    test_python["list"] = ["a"]
    value = csv_helper.serialize_value("header", test_python)
    assert value == "{key:value;dict:{nkey:nvalue};list:[a]}"


def test_csv_serialize_list_nested(csv_helper):
    """Test csv helper with list containing nested list/dict."""
    test_python = ["value", {"nkey": "nvalue"}, ["a"]]
    value = csv_helper.serialize_value("header", test_python)
    assert value == "[value;{nkey:nvalue};[a]]"


def test_csv_serialize_ansible_value(csv_helper):
    """Test csv helper with ansible dict."""
    test_python = {"rc": 0}
    value = csv_helper.serialize_value("header", test_python)
    assert value == CSVHelper.ANSIBLE_ERROR_MESSAGE


def test_csv_generate_headers(csv_helper):
    """Test csv_generate_headers method."""
    fact_list = [
        {"header1": "value1"},
        {"header2": "value2"},
        {"header1": "value2", "header3": "value3"},
    ]
    headers = CSVHelper.generate_headers(fact_list)
    expected_headers = {"header1", "header2", "header3"}
    assert set(headers) == expected_headers


def test_create_tar_buffer(csv_helper):
    """Test create_tar_buffer method."""
    files_data = {
        "test0.json": {"id": 1, "report": [{"key": "value"}]},
        "test1.json": {"id": 2, "report": [{"key": "value"}]},
    }
    # create tar buffer expects encoded data
    files_data_encoded = {
        file_name: encode_content(data, "json")
        for file_name, data in files_data.items()
    }
    tar_buffer = create_tar_buffer(files_data_encoded)
    assert isinstance(tar_buffer, io.BytesIO)
    assert "getvalue" in dir(tar_buffer)
    with tarfile.open(fileobj=tar_buffer) as tar:
        files = tar.getmembers()
        assert files != []
        assert len(files) == 2
        for file_obj in files:
            file = tar.extractfile(file_obj)
            extracted_content = json.loads(file.read().decode())
            assert extracted_content in files_data.values()


def test_bad_param_type_create_tar_buffer(csv_helper):
    """Test passing in a non-list into create_tar_buffer."""
    json_list = [
        "{'id': 1, 'report': [{'key': 'value'}]}",
        "{'id': 2, 'report': [{'key': 'value'}]}",
    ]
    tar_result = create_tar_buffer(json_list)
    assert tar_result is None


def test_bad_dict_contents_type_create_tar_buffer(csv_helper):
    """Test passing in a list of json into create_tar_buffer."""
    json0 = {"id.csv": 1, "report": [{"key.csv": "value"}]}
    tar_result = create_tar_buffer(json0)
    assert tar_result is None


def test_extract_tar_gz_content_good(csv_helper):
    """Test extracting files by passing a BytesIO object."""
    files_data = {
        "test0.json": {"id": 1, "report": [{"key": "value"}]},
        "test1.json": {"id": 2, "report": [{"key": "value"}]},
    }
    # create tar buffer expects encoded data
    files_data_encoded = {
        file_name: encode_content(data, "json")
        for file_name, data in files_data.items()
    }
    tar_buffer = create_tar_buffer(files_data_encoded)
    assert isinstance(tar_buffer, io.BytesIO)
    extracted_files = extract_files_from_tarball(
        tar_buffer, strip_dirs=False, decode_json=True
    )
    assert set(extracted_files.keys()) == set(files_data.keys())
    for extracted_name, extracted_data in extracted_files.items():
        assert extracted_data == files_data[extracted_name]
