"""Utility functions to help tests for API reports."""

import tarfile
from io import BytesIO
from pathlib import Path

from requests import Response


def extract_tarball_from_response(
    response: Response, strip_dirs: bool = True
) -> dict[str, bytes]:
    r"""
    Extract the files from a response tarball.

    Note that the returned dict has file contents as raw bytes, not decoded strings.

    Example return value:

        {
            "message.txt": b"hello world\n",
            "data.csv": b"id,name\n420,potato\n",
            "data.json": b'{"id":420,"name":"potato"}\n',
        }

    :param response: full Response object from a request
    :param strip_dirs: if True, strip the parent directories from the filename keys
    :return: dict containing file contents keyed by filename
    """
    with tarfile.open(fileobj=BytesIO(response.content)) as tarball:
        return dict(
            [
                (
                    Path(filepath).name if strip_dirs else filepath,
                    tarball.extractfile(filepath).read(),
                )
                for filepath in tarball.getnames()
            ]
        )
