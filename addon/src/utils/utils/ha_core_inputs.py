# ha_core_inputs.py
# Utility functions for Home Assistant core input file detection, preference, and loading.
#
# TODO (@Strategos): Embed this logic into the main registry ingestion pipeline and config management.
# - Integrate input source selection and file loading into registry generation scripts.
# - Ensure environment/config flags are respected for authoritative vs stored input selection.
# - Document usage in pipeline README and contract.

import json
import os
from pathlib import Path


def is_ha_core_input_available(
    core_path="/Volumes/config/.storage/core.entity_registry",
):
    """
    Returns True if the Home Assistant core input file exists at the given path.
    """
    return Path(core_path).exists()


def prefer_authoritative_input():
    """
    Returns True if scripting logic should ingest authoritative input files direct from config source.
    Returns False if scripts should use stored file versions.
    Uses environment variable OMEGA_USE_AUTHORITATIVE_INPUT ("true"/"false").
    """
    return os.environ.get("OMEGA_USE_AUTHORITATIVE_INPUT", "false").lower() == "true"


def load_ha_core_registry(core_path="/Volumes/config/.storage/core.entity_registry"):
    """
    Loads and returns the Home Assistant core entity registry from the given path.
    Returns None if file is not found or cannot be loaded.
    """
    core_file = Path(core_path)
    if not core_file.exists():
        return None
    try:
        with open(core_file, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load {core_path}: {e}")
        return None


def list_ha_core_storage_files(storage_dir="/Volumes/config/.storage"):
    """
    Returns a list of all files in the Home Assistant core storage directory.
    Useful for discovering available core registry/config docs.
    """
    storage_path = Path(storage_dir)
    if not storage_path.exists() or not storage_path.is_dir():
        return []
    return [str(p) for p in storage_path.iterdir() if p.is_file()]


# Example usage:
# Discover available core registry/config docs and load one
ha_core_files = list_ha_core_storage_files()
if ha_core_files:
    # Example: load the first available registry file
    registry_data = load_ha_core_registry(core_path=ha_core_files[0])
    # registry_data now contains the loaded JSON, or None if failed
