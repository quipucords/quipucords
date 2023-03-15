"""get_scanner module."""

import importlib


def get_scanner(data_source):
    """Get the appropriate scanner for given data_source."""
    try:
        return importlib.import_module(f"scanner.{data_source}")
    except ModuleNotFoundError as error:
        raise NotImplementedError(f"Unsupported source type: {data_source}") from error
