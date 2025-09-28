"""Top-level utils package for addon.src

This module provides a small set of compatibility re-exports to preserve
pre-migration import paths used across the codebase. Per ADR-0003 we do not
perform any I/O at import time here; this file only exposes symbols from the
deeper `utils` subpackage.
"""

# Re-export commonly-used helpers for compatibility with older import paths.
from .utils.import_path import set_workspace_root  # re-export helper
from .utils import pipeline_config  # re-export pipeline configuration loader
from .utils import file_utils  # re-export small file utility helpers

__all__ = ["set_workspace_root", "pipeline_config", "file_utils"]
