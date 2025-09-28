"""Compatibility shim for `addon.src.utils.input_list_extract`.

Re-exports the `extract_data` function from the deeper utils package.
"""

from .utils.input_list_extract import extract_data

__all__ = ["extract_data"]
