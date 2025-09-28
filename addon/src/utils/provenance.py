"""Compatibility shim for `addon.src.utils.provenance`.

Re-export provenance utilities from the deeper utils package.
"""

from .utils.provenance import file_sha256, read_manifest, write_manifest

__all__ = ["file_sha256", "read_manifest", "write_manifest"]
