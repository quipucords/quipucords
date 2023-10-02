"""Utility functions to help tests for API reports."""
import json
import tarfile
from io import BytesIO
from pathlib import Path

from requests import Response


def extract_tarball_from_response(
    response: Response, strip_dirs: bool = True, decode_json: bool = False
) -> dict[str, bytes]:
    r"""
    Extract the files from a response tarball.

    Note that the returned dict normally contains each file's contents as raw bytes,
    not decoded strings. Setting decode_json=True will attempt to decode all contents
    as strings and JSON.loads them.

    Example default return value:

        {
            "message.txt": b"hello world\n",
            "data.csv": b"id,name\n420,potato\n",
            "data.json": b'{"id":420,"name":"potato"}\n',
        }

    :param response: full Response object from a request
    :param strip_dirs: if True, strip the parent directories from the filename keys
    :param decode_json: if True, assume all files are JSON, and return them as decoded
        objects instead of raw bytes
    :return: dict containing file contents keyed by filename
    """
    with tarfile.open(fileobj=BytesIO(response.content)) as tarball:
        return dict(
            [
                (
                    Path(filepath).name if strip_dirs else filepath,
                    json.loads(tarball.extractfile(filepath).read().decode())
                    if decode_json
                    else tarball.extractfile(filepath).read(),
                )
                for filepath in tarball.getnames()
            ]
        )
