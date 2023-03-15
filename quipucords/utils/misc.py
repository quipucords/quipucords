"""Misc utils for quipucords."""
import json


def load_json_from_tarball(json_filename, tarball):
    """Extract a json as dict from given TarFile interface."""
    return json.loads(tarball.extractfile(json_filename).read())
