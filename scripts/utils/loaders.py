# PATCH-CANONICAL-LOADERS-V1: Shared YAML loader utility for all contract-driven logic
#
# This file was created as part of a workspace-wide refactor to ensure all YAML loading
# for registry, contract, and analytics files is performed through a single, auditable function.
# Motivation: Eliminate duplicate loader logic, guarantee consistent parsing, and provide a
# single point of patch/audit for all contract-driven scripts (e.g., registry generators,
# contract enforcers, analytics pipelines). All scripts should import load_yaml from this file.
#
# Integration: As of 2025-07-23, all references to load_yaml in generate_omega_registry.py and
# output_contract_enforcer.py have been redirected to this canonical utility. Future changes to
# YAML parsing, error handling, or audit logging should be made here for full traceability.
#
# For audit: See copilot_chat_output.log and patch comments in all affected scripts for lineage.

import json
import os
from typing import Any

import yaml

from scripts.utils.input_list_extract import extract_data


def load_yaml(path: str) -> Any:
    """
    PATCH-CANONICAL-LOADERS-V1: Canonical YAML loader for registry and contract files.
    All contract-driven scripts should import this function for auditability and traceability.
    Args:
        path (str): Path to the YAML file to load.
    Returns:
        Any: Parsed YAML content (dict, list, etc.)
    """
    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_json_with_extract(path: str):
    """
    Canonical JSON loader for registry files. Always uses extract_data to normalize structure.
    Args:
        path (str): Path to the JSON file to load.
    Returns:
        list: List of dict entries (normalized)
    """
    if not path or not isinstance(path, str):
        return []
    if not os.path.exists(path):
        print(f"[WARN] Missing input: {path}")
        return []
    with open(path, "r") as f:
        content = json.load(f)
    entries = extract_data(path, content)
    entries = [e for e in entries if isinstance(e, dict)]
    if not entries:
        print(f"[WARN] No valid dict entries extracted from: {path}")
    return entries


# Usage: Replace all direct json.load for registry files with load_json_with_extract.
# PATCH END: All YAML loading for contract-driven logic is now routed through this function.
