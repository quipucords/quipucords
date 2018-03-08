#
# Copyright (c) 2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test the common util."""

from collections import OrderedDict
from django.test import TestCase
from api.common.util import CSVHelper


class CommonUtilTest(TestCase):
    """Tests common util functions."""

    # pylint: disable=no-self-use,too-many-arguments,invalid-name
    # pylint: disable=too-many-locals,too-many-branches

    def setUp(self):
        """Create test case setup."""
        self.csv_helper = CSVHelper()

    def test_csv_serialize_empty_values(self):
        """Test csv helper with empty values."""
        # Test Empty case
        value = self.csv_helper.serialize_value('header', {})
        self.assertEqual('', value)
        value = self.csv_helper.serialize_value('header', [])
        self.assertEqual('', value)

    def test_csv_serialize_dict_1_key(self):
        """Test csv helper with 1 key dict."""
        # Test flat 1 entry
        test_python = {'key': 'value'}
        value = self.csv_helper.serialize_value('header', test_python)
        self.assertEqual(value, '{key:value}')

    def test_csv_serialize_list_1_value(self):
        """Test csv helper with 1 item list."""
        test_python = ['value']
        value = self.csv_helper.serialize_value('header', test_python)
        self.assertEqual(value, '[value]')

    def test_csv_serialize_dict_2_keys(self):
        """Test csv helper with 2 key dict."""
        # Test flat with 2 entries
        test_python = OrderedDict()
        test_python['key1'] = 'value1'
        test_python['key2'] = 'value2'
        value = self.csv_helper.serialize_value('header', test_python)
        self.assertEqual(value, '{key1:value1,key2:value2}')

    def test_csv_serialize_list_2_values(self):
        """Test csv helper with 2 item list."""
        test_python = ['value1', 'value2']
        value = self.csv_helper.serialize_value('header', test_python)
        self.assertEqual(value, '[value1;value2]')

    def test_csv_serialize_dict_nested(self):
        """Test csv helper with dict containing nested list/dict."""
        # Test nested
        test_python = OrderedDict()
        test_python['key'] = 'value'
        test_python['dict'] = {'nkey': 'nvalue'}
        test_python['list'] = ['a']
        value = self.csv_helper.serialize_value('header', test_python)
        self.assertEqual(value, '{key:value,dict:{nkey:nvalue},list:[a]}')

    def test_csv_serialize_list_nested(self):
        """Test csv helper with list containing nested list/dict."""
        test_python = ['value', {'nkey': 'nvalue'}, ['a']]
        value = self.csv_helper.serialize_value('header', test_python)
        self.assertEqual(value, '[value;{nkey:nvalue};[a]]')

    def test_csv_serialize_ansible_value(self):
        """Test csv helper with ansible dict."""
        # Test ansible error
        test_python = {'rc': 0}
        value = self.csv_helper.serialize_value('header', test_python)
        self.assertEqual(
            value, CSVHelper.ANSIBLE_ERROR_MESSAGE)

    def test_csv_generate_headers(self):
        """Test csv_generate_headers method."""
        fact_list = [{'header1': 'value1'},
                     {'header2': 'value2'},
                     {'header1': 'value2',
                      'header3': 'value3'}]
        headers = CSVHelper.generate_headers(fact_list)
        self.assertEqual(3, len(headers))
        expected = set(['header1', 'header2', 'header3'])
        self.assertSetEqual(expected, set(headers))
