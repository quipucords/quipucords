"""Utility functions to help tests for API reports."""
import json
import tarfile
from io import BytesIO
from pathlib import Path


def extract_files_from_tarball(
    tarball_data: bytes | BytesIO, strip_dirs: bool = True, decode_json: bool = False
) -> dict[str, bytes]:
    r"""
    Extract all files contained within an in-memory tarball (.tar.gz) file.

    Note that the returned dict normally contains each file's contents as raw bytes,
    not decoded strings. Setting decode_json=True will attempt to decode all contents
    as strings and JSON.loads them.

    Example default return value:

        {
            "message.txt": b"hello world\n",
            "data.csv": b"id,name\n420,potato\n",
            "data.json": b'{"id":420,"name":"potato"}\n',
        }

    :param tarball_data: bytes or BytesIO representation of a tarball
    :param strip_dirs: if True, strip the parent directories from the filename keys
    :param decode_json: if True, decode files with .json extension.
    :return: dict containing file contents keyed by filename
    """
    if not isinstance(tarball_data, BytesIO):
        tarball_data = BytesIO(tarball_data)
    with tarfile.open(fileobj=tarball_data) as tarball_file:
        return dict(
            [
                (
                    Path(filepath).name if strip_dirs else filepath,
                    json.loads(tarball_file.extractfile(filepath).read().decode())
                    if decode_json and filepath.lower().endswith(".json")
                    else tarball_file.extractfile(filepath).read(),
                )
                for filepath in tarball_file.getnames()
            ]
        )
