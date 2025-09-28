"""Compatibility shim for `addon.src.utils.import_path`.

This file re-exports the `set_workspace_root` helper from the
`addon.src.utils.utils.import_path` module so older absolute imports continue
to work after we restructured the package.
"""

from .utils.import_path import set_workspace_root

__all__ = ["set_workspace_root"]
