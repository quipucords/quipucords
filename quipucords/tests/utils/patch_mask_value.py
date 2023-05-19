"""Context manager to patch 'mask_value' utility."""

from contextlib import contextmanager
from unittest import mock

from api.common import util


@contextmanager
def patch_mask_value(replace_values: dict):
    """Patch 'mask_value' utility."""

    def _patched_mask_value(value):
        return replace_values[value]

    with mock.patch.object(util, "mask_value", _patched_mask_value) as patched_fn:
        yield patched_fn
