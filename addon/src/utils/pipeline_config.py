"""Compatibility shim for `addon.src.utils.pipeline_config`.

Re-export constants and helpers from `addon.src.utils.utils.pipeline_config`.
"""

from .utils.pipeline_config import *  # re-export all configuration constants

__all__ = [k for k in dir() if not k.startswith("_")]
