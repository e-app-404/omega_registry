from pathlib import Path

# Lightweight, import-safe path resolver for ADR-0005 workspace canonicalization.
# This module must not perform any I/O on import (ADR-0003 compliance).

# PROJECT_ROOT points to the repository root. From this file (addon/src/utils/paths.py)
# the parents chain is: paths.py -> utils -> src -> addon -> <repo root>
PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]

# Preferred support location per ADR-0005
ADDON_SUPPORT: Path = PROJECT_ROOT / "addon" / "support"

# Fallback location where contracts currently live in some branches
FALLBACK_SUPPORT: Path = (
    PROJECT_ROOT / "addon" / "data" / "canonical" / "support"
)


def support_path(*parts: str) -> Path:
    """Return a Path under addon/support if present, else under addon/data/canonical/support.

    This function performs no file reads, but will construct a Path that prefers the
    ADR-0005 location while remaining compatible with the existing layout.
    """
    if parts:
        preferred = ADDON_SUPPORT.joinpath(*parts)
        fallback = FALLBACK_SUPPORT.joinpath(*parts)
    else:
        preferred = ADDON_SUPPORT
        fallback = FALLBACK_SUPPORT
    # Prefer the ADR-0005 location; calling code can check existence if needed.
    return preferred if preferred.exists() else fallback


def get_contract_path(name: str) -> Path:
    """Return a Path for a contract file under addon/support/contracts/ (with fallback)."""
    return support_path("contracts", name)


def get_contract_str(name: str) -> str:
    return str(get_contract_path(name))


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
