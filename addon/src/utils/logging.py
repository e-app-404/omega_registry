"""Compatibility shim for `addon.src.utils.logging`.

Re-exports logging helpers from `addon.src.utils.utils.logging`.
No I/O should occur at import time; this module only exposes symbols.
"""

from .utils.logging import setup_logging, attach_meta

__all__ = ["setup_logging", "attach_meta"]
