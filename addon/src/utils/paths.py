"""
Canonical path resolution for Omega Registry.
Import-safe path helpers following ADR-0003 and ADR-0005.
"""
from pathlib import Path
from typing import Union

# Base paths (computed at import time, no I/O)
ADDON_ROOT = Path(__file__).parent.parent.parent
PROJECT_ROOT = ADDON_ROOT.parent
ADDON_SRC = ADDON_ROOT / "src"
ADDON_DATA = ADDON_ROOT / "data"

def get_data_path(relative_path: Union[str, Path] = "") -> Path:
    """Get path in addon/data/ directory."""
    return ADDON_DATA / relative_path

def get_input_path(relative_path: Union[str, Path] = "") -> Path:
    """Get path in addon/data/input/ directory."""
    return ADDON_DATA / "input" / relative_path

def get_output_path(relative_path: Union[str, Path] = "") -> Path:
    """Get path in addon/data/output/ directory."""
    return ADDON_DATA / "output" / relative_path

def get_registry_path(relative_path: Union[str, Path] = "") -> Path:
    """Get path in addon/data/registry/ directory."""
    return ADDON_DATA / "registry" / relative_path

def get_support_path(relative_path: Union[str, Path] = "") -> Path:
    """Get path in addon/support/ directory."""
    return ADDON_ROOT / "support" / relative_path

def get_project_path(relative_path: Union[str, Path] = "") -> Path:
    """Get path in project/ directory."""
    return PROJECT_ROOT / "project" / relative_path

