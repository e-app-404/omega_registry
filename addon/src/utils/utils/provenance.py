"""Provenance helper utilities.

Centralizes SHA256, timezone-aware timestamps, and provenance manifest I/O so
writers and the pipeline share the same behavior.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def compute_sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def file_sha256(path: str | Path) -> str:
    p = Path(path)
    h = hashlib.sha256()
    with p.open("rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def tz_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_manifest(manifest_env: Optional[str] = None) -> Dict[str, Any]:
    path = (
        manifest_env
        or os.getenv("OMEGA_PROVENANCE_MANIFEST")
        or "canonical/omega_registry_master.provenance.json"
    )
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_manifest(
    manifest: Dict[str, Any], manifest_env: Optional[str] = None
) -> None:
    path = (
        manifest_env
        or os.getenv("OMEGA_PROVENANCE_MANIFEST")
        or "canonical/omega_registry_master.provenance.json"
    )
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def upsert_manifest_entry(
    key: str, entry: Dict[str, Any], manifest_env: Optional[str] = None
) -> None:
    """Insert or update a manifest entry under `key` (string path).

    Uses the manifest determined via OMEGA_PROVENANCE_MANIFEST or the canonical path.
    The key SHOULD be an absolute path to avoid ambiguity.
    """
    manifest = read_manifest(manifest_env)
    manifest[key] = entry
    write_manifest(manifest, manifest_env)
