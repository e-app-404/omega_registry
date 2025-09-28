"""Compatibility stub for scripts.utils.input_list_extract.

Re-exports functions from addon.src.utils.input_list_extract to maintain
compatibility with legacy project ops scripts during ADR-0005 migration.
"""

from addon.src.utils.input_list_extract import extract_data

__all__ = ["extract_data"]
