"""Misc utils for quipucords."""
import json


def get_choice_ids(choices):
    """Retrieve choice ids."""
    return [choice[0] for choice in choices]


def load_json_from_tarball(json_filename, tarball):
    """Extract a json as dict from given TarFile interface."""
    return json.loads(tarball.extractfile(json_filename).read())
