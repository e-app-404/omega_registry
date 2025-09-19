"""
import_path.py
Utility for setting workspace-root sys.path for robust script imports.
Usage:
    from scripts.utils.import_path import set_workspace_root
    set_workspace_root(__file__)
"""

import sys
from pathlib import Path


def set_workspace_root(current_file):
    """
    Ensures workspace root is in sys.path for robust imports.
    Args:
        current_file (str): __file__ of the calling script.
    """
    root = str(Path(current_file).parent.parent.parent)
    if root not in sys.path:
        sys.path.insert(0, root)
