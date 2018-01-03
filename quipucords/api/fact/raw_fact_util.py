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

"""Util to read/write raw facts to file"""

import os
import json
import copy
from django.conf import settings


def read_raw_facts(fc_id):
    """Read raw facts from json file.

    :param fc_id: Fact collection id to read
    "returns: JSON data as dict or None if invalid fc_id
    """
    if os.path.exists(settings.FACTS_DIR):
        with open(_build_path(fc_id), 'r') as raw_fact_file:
            data = json.load(raw_fact_file)
            return data

    return None


def write_raw_facts(fc_id, data):
    """Write raw facts to json file.

    :param fc_id: Fact collection id to write
    :param data: JSON data as dict to write
    "returns: Fully qualified path to json file
    """
    if not os.path.exists(settings.FACTS_DIR):
        os.makedirs(settings.FACTS_DIR)

    file_path = _build_path(fc_id)
    data_copy = copy.deepcopy(data)
    data_copy['fact_collection_id'] = fc_id
    with open(file_path, 'w') as raw_fact_file:
        json.dump(data_copy, raw_fact_file)

    return file_path


def _build_path(fc_id):
    """Helper to consistently build path."""
    return '%s/%d.json' % (settings.FACTS_DIR, fc_id)
