"""
Common utils for quipucords.

All utils should be imported here so the internal api for importing is just
"from utils import some_util_func".
"""

from .deepget import deepget
from .default_getter import default_getter
from .get_from_object_or_dict import get_from_object_or_dict
from .misc import load_json_from_tarball
