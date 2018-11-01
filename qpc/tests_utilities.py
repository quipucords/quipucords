#
# Copyright (c) 2017-2018 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# https://www.gnu.org/licenses/gpl-3.0.txt.
#
"""Test utilities for the CLI module."""

import contextlib
import io
import json
import sys
import tarfile
import uuid


DEFAULT_CONFIG = {'host': '127.0.0.1', 'port': 8000, 'use_http': True}


# pylint: disable=too-few-public-methods
class HushUpStderr():
    """Class used to quiet standard error output."""

    def write(self, stream):
        """Ignore standard error output."""
        pass


@contextlib.contextmanager
def redirect_stdout(stream):
    """Run a code block, capturing stdout to the given stream."""
    old_stdout = sys.stdout
    try:
        sys.stdout = stream
        yield
    finally:
        sys.stdout = old_stdout


def create_tar_buffer(data_array):
    """Generate a tar buffer when data_array is list of json.

    :param data_array: A list of json.
    """
    if not isinstance(data_array, (list,)):
        return None
    for data in data_array:
        if not isinstance(data, (dict,)):
            return None
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar_file:
        for data in data_array:
            json_buffer = io.BytesIO(json.dumps(data).encode('utf-8'))
            json_name = '%s.json' % str(uuid.uuid4())
            info = tarfile.TarInfo(name=json_name)
            info.size = len(json_buffer.getvalue())
            tar_file.addfile(tarinfo=info, fileobj=json_buffer)
    tar_buffer.seek(0)
    return tar_buffer.getvalue()
