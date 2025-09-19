"""
PATCH-OMEGA-REGISTRY-REFACTOR-V1: Loader logic for omega registry inputs.
Loads raw input data (entity registry, device registry, area registry, etc.).
"""

import json
import os

from scripts.utils.input_list_extract import extract_data


def load_json(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    if path.endswith(".json"):
        alt_path = path[:-5]
        if os.path.exists(alt_path):
            with open(alt_path) as f:
                return json.load(f)
    print(f"[WARN] Missing input: {path}")
    return None


def load_json_with_extract(path):
    content = load_json(path)
    if content is None:
        return []
    entries = extract_data(path, content)
    # Only keep dicts for registry entities
    entries = [e for e in entries if isinstance(e, dict)]
    if not entries:
        print(f"[WARN] No valid dict entries extracted from: {path}")
    return entries
