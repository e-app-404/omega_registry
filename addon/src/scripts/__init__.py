"""Compatibility package to expose `scripts.*` imports.

This package proxies the `scripts` top-level imports to the reorganized
`addon.src.scripts` package. Keep this shim minimal — it only exposes the
`enrich` subpackage which the registry generator expects.
"""

"""Compatibility package to expose `scripts.*` imports.

This module intentionally avoids performing eager imports to prevent
deep import cascades when the package is imported. Use explicit imports
where needed (e.g., within runtime functions) to keep imports import-safe.
"""

__all__ = []
