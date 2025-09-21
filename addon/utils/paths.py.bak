"""Workspace path helpers.

This module centralizes path resolution so scripts can use canonical_path(...)
and repo-relative paths in a consistent, testable way. It prefers an
environment override `CANONICAL_ROOT` when present, and provides backwards
compatibility if the addon directory is still named `registry_rehydration_local_last`.

Usage examples:
        from utils.paths import canonical_path, addon_root
        p = canonical_path('registry_inputs', 'core.entity_registry')

The helpers attempt to discover the repository root by walking parents until
a `.git` directory is found. If that fails, current working directory is used.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Union


def find_repo_root(start: Union[str, Path] | None = None) -> Path:
    """Walk up from start until a directory containing .git is found.

    If none is found, fall back to the current working directory.
    """
    if start is None:
        p = Path(__file__).resolve()
    else:
        p = Path(start).resolve()

    for parent in [p] + list(p.parents):
        if (parent / ".git").exists():
            return parent

    return Path.cwd()


def repo_root() -> Path:
    return find_repo_root()


def addon_root() -> Path:
    """Return the addon directory path.

    Prefer a directory named `addon` at the repo root. For backward
    compatibility, fall back to `registry_rehydration_local_last` if present.
    """
    r = repo_root()
    cand = r / "addon"
    if cand.exists():
        return cand
    alt = r / "registry_rehydration_local_last"
    return alt if alt.exists() else cand


def canonical_root() -> Path:
    """Return the canonical data root.

    Respects the CANONICAL_ROOT environment variable, otherwise resolves to
    `<repo_root>/canonical` or `<addon_root>/canonical` (addon wins if present).
    """
    env = os.getenv("CANONICAL_ROOT")
    if env:
        return Path(env)

    a = addon_root() / "canonical"
    if a.exists():
        return a

    return repo_root() / "canonical"


def canonical_path(*parts: str) -> Path:
    """Return an absolute Path inside the canonical root."""
    return canonical_root().joinpath(*parts).resolve()


def resolve_repo(*parts: str) -> Path:
    """Return an absolute Path inside the repository root."""
    return repo_root().joinpath(*parts).resolve()


def info() -> dict:
    """Return debugging info about the current resolved roots."""
    return {
        "repo_root": str(repo_root()),
        "addon_root": str(addon_root()),
        "canonical_root": str(canonical_root()),
    }


__all__ = [
    "find_repo_root",
    "repo_root",
    "addon_root",
    "canonical_root",
    "canonical_path",
    "resolve_repo",
    "info",
]
