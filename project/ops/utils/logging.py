"""Compatibility stub for scripts.utils.logging.

Re-exports functions from addon.src.utils.logging to maintain compatibility
with legacy project ops scripts during ADR-0005 migration.
"""

from addon.src.utils.logging import setup_logging, attach_meta


# Additional legacy function that some scripts expect
def write_json_log(*args, **kwargs):
    """Stub for write_json_log - delegate to setup_logging for now."""
    # This was likely a specialized logging function
    # For now, just pass through to standard logging setup
    return setup_logging(*args, **kwargs)


__all__ = ["setup_logging", "attach_meta", "write_json_log"]
