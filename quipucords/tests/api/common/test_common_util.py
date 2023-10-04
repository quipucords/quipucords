"""Test the common util."""

import io
import json
import tarfile
from collections import OrderedDict

from django.test import TestCase

from api.common.common_report import CSVHelper, create_tar_buffer, encode_content
from tests.report_utils import extract_files_from_tarball


class CommonUtilTest(TestCase):
    """Tests common util functions."""

    def setUp(self):
        """Create test case setup."""
        self.csv_helper = CSVHelper()

    def test_csv_serialize_empty_values(self):
        """Test csv helper with empty values."""
        # Test Empty case
        value = self.csv_helper.serialize_value("header", {})
        self.assertEqual("", value)
        value = self.csv_helper.serialize_value("header", [])
        self.assertEqual("", value)

    def test_csv_serialize_dict_1_key(self):
        """Test csv helper with 1 key dict."""
        # Test flat 1 entry
        test_python = {"key": "value"}
        value = self.csv_helper.serialize_value("header", test_python)
        self.assertEqual(value, "{key:value}")

    def test_csv_serialize_list_1_value(self):
        """Test csv helper with 1 item list."""
        test_python = ["value"]
        value = self.csv_helper.serialize_value("header", test_python)
        self.assertEqual(value, "[value]")

    def test_csv_serialize_dict_2_keys(self):
        """Test csv helper with 2 key dict."""
        # Test flat with 2 entries
        test_python = OrderedDict()
        test_python["key1"] = "value1"
        test_python["key2"] = "value2"
        value = self.csv_helper.serialize_value("header", test_python)
        self.assertEqual(value, "{key1:value1;key2:value2}")

    def test_csv_serialize_list_2_values(self):
        """Test csv helper with 2 item list."""
        test_python = ["value1", "value2"]
        value = self.csv_helper.serialize_value("header", test_python)
        self.assertEqual(value, "[value1;value2]")

    def test_csv_serialize_dict_nested(self):
        """Test csv helper with dict containing nested list/dict."""
        # Test nested
        test_python = OrderedDict()
        test_python["key"] = "value"
        test_python["dict"] = {"nkey": "nvalue"}
        test_python["list"] = ["a"]
        value = self.csv_helper.serialize_value("header", test_python)
        self.assertEqual(value, "{key:value;dict:{nkey:nvalue};list:[a]}")

    def test_csv_serialize_list_nested(self):
        """Test csv helper with list containing nested list/dict."""
        test_python = ["value", {"nkey": "nvalue"}, ["a"]]
        value = self.csv_helper.serialize_value("header", test_python)
        self.assertEqual(value, "[value;{nkey:nvalue};[a]]")

    def test_csv_serialize_ansible_value(self):
        """Test csv helper with ansible dict."""
        # Test ansible error
        test_python = {"rc": 0}
        value = self.csv_helper.serialize_value("header", test_python)
        self.assertEqual(value, CSVHelper.ANSIBLE_ERROR_MESSAGE)

    def test_csv_generate_headers(self):
        """Test csv_generate_headers method."""
        fact_list = [
            {"header1": "value1"},
            {"header2": "value2"},
            {"header1": "value2", "header3": "value3"},
        ]
        headers = CSVHelper.generate_headers(fact_list)
        self.assertEqual(3, len(headers))
        expected = set(["header1", "header2", "header3"])
        self.assertSetEqual(expected, set(headers))

    def test_create_tar_buffer(self):
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
        self.assertIsInstance(tar_buffer, (io.BytesIO))
        self.assertIn("getvalue", dir(tar_buffer))
        with tarfile.open(fileobj=tar_buffer) as tar:
            files = tar.getmembers()
            self.assertNotEqual(files, [])
            self.assertEqual(2, len(files))
            for file_obj in files:
                file = tar.extractfile(file_obj)
                extracted_content = json.loads(file.read().decode())
                self.assertIn(extracted_content, files_data.values())

    def test_bad_param_type_create_tar_buffer(self):
        """Test passing in a non-list into create_tar_buffer."""
        json_list = [
            "{'id': 1, 'report': [{'key': 'value'}]}",
            "{'id': 2, 'report': [{'key': 'value'}]}",
        ]
        tar_result = create_tar_buffer(json_list)
        self.assertEqual(tar_result, None)

    def test_bad_dict_contents_type_create_tar_buffer(self):
        """Test passing in a list of json into create_tar_buffer."""
        json0 = {"id.csv": 1, "report": [{"key.csv": "value"}]}
        tar_result = create_tar_buffer(json0)
        self.assertEqual(tar_result, None)

    def test_extract_tar_gz_content_good(self):
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
        self.assertIsInstance(tar_buffer, io.BytesIO)
        extracted_files = extract_files_from_tarball(
            tar_buffer, strip_dirs=False, decode_json=True
        )
        self.assertEqual(set(extracted_files.keys()), set(files_data.keys()))
        for extracted_name, extracted_data in extracted_files.items():
            self.assertEqual(extracted_data, files_data[extracted_name])
