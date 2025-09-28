#!/usr/bin/env python3
"""
Run as module: python -m scripts.generators.sanitize_alpha_room_registry
PATCH ABSOLUTE-IMPORT-UTILS-V1: Refactored for absolute imports, removed sys.path hacks, added run-as-module comment.
"""

import argparse
import json
import logging
from collections import defaultdict
from pathlib import Path

import yaml

from addon.src.utils.logging import setup_logging
from addon.src.utils.paths import get_contract_str

# Module-level placeholders to keep import-time safe
LOG = None
output_contract = None
output_contract_raw = None
ENTITY_FLATMAP_PATH = Path(
    "canonical/derived_views/flatmaps/entity_flatmap.json"
)


def _load_output_contract(path_str: str):
    """Load an output contract from disk if available, return normalized dict."""
    global output_contract_raw, output_contract
    output_contract_raw = None
    output_contract = None

    if not path_str:
        return None

    p = Path(path_str)
    if not p.exists():
        # missing contract is non-fatal here; return None to let caller decide
        return None

    try:
        with p.open("r", encoding="utf-8") as f:
            output_contract_raw = yaml.safe_load(f)
    except Exception:
        output_contract_raw = None

    if isinstance(output_contract_raw, list):
        # normalize to dict form
        output_contract = {
            item.get("name"): item
            for item in output_contract_raw
            if isinstance(item, dict)
        }
    else:
        output_contract = output_contract_raw

    return output_contract


def sanitize_from_flatmap(entity_flatmap_path: str, out_path: str):
    """Sanitize alpha room registry from an entity flatmap

    This function assumes file I/O has been validated by the caller. It will
    raise FileNotFoundError if the input flatmap is missing.
    """
    global LOG
    if LOG is None:
        LOG = logging.getLogger("sanitize_alpha_room_registry")

    LOG.info("Starting sanitize_from_flatmap")

    ent_path = Path(entity_flatmap_path)
    if not ent_path.exists():
        raise FileNotFoundError(
            f"Entity flatmap not found: {entity_flatmap_path}"
        )

    with ent_path.open("r", encoding="utf-8") as f:
        flatmap = json.load(f)

    # Minimal example: produce an output that lists rooms found in the flatmap
    rooms = defaultdict(list)
    for ent_id, ent in flatmap.items():
        room = ent.get("area_id") or "unknown"
        rooms[room].append(ent_id)

    out_p = Path(out_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with out_p.open("w", encoding="utf-8") as f:
        json.dump({"rooms": {k: len(v) for k, v in rooms.items()}}, f, indent=2)

    LOG.info("Sanitize complete; output written to %s", out_path)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--entity-flatmap", default=str(ENTITY_FLATMAP_PATH))
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    # setup logging
    global LOG
    LOG = setup_logging("tools/sanitize_alpha_room_registry")

    # load output contract if present (non-fatal)
    contract_path = get_contract_str(
        "omega_registry_master.output_contract.yaml"
    )
    _load_output_contract(contract_path)

    # run
    return sanitize_from_flatmap(args.entity_flatmap, args.out)


if __name__ == "__main__":
    main()
