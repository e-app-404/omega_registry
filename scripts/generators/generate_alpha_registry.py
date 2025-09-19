#!/usr/bin/env python3
"""
Run as module: python -m scripts.generators.generate_alpha_registry
PATCH ABSOLUTE-IMPORT-UTILS-V1: Refactored for absolute imports, removed sys.path hacks, added run-as-module comment.
"""

"""
PATCH-ALPHA-REGISTRY-CONSOLIDATION-V1
Merged alpha room registry logic from generate_alpha_room_registry.py.

Supports --type room or --target alpha_room_registry CLI argument.

Modularized main logic for contract alignment and maintainability.
"""

import argparse
import json
import logging
from collections import defaultdict
from pathlib import Path

import yaml

from scripts.utils.import_path import set_workspace_root
from scripts.utils.logging import setup_logging

set_workspace_root(__file__)

from scripts.utils.input_list_extract import extract_data
from scripts.utils.logging import attach_meta
from scripts.utils.pipeline_config import (
    AREA_REGISTRY,
    ENTITY_SOURCE,
    FLOOR_REGISTRY,
    METRICS_FILE,
)

# Helper to load JSON


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


# Load inputs using robust extraction
OMEGA_ROOM_REG = "canonical/omega_registry_master.json"
omega_rooms = extract_data(OMEGA_ROOM_REG, load_json(OMEGA_ROOM_REG))
floor_registry = extract_data(str(FLOOR_REGISTRY), load_json(str(FLOOR_REGISTRY)))
area_registry = extract_data(str(AREA_REGISTRY), load_json(str(AREA_REGISTRY)))
metrics = load_json(METRICS_FILE)
entity_data = extract_data(ENTITY_SOURCE, load_json(ENTITY_SOURCE))

# Tiers by area
tiers_by_area = metrics.get("area_floor_analytics", {}).get("tiers_by_area", {})

# Build floor map
floor_map = {}
for floor in floor_registry:
    for area_id in floor.get("areas", []):
        floor_map[area_id] = floor["floor_id"]

# Organize entities by area/domain/device_class
entities_by_area = defaultdict(dict)
for e in entity_data:
    area = e.get("area_id")
    domain = e.get("domain")
    dev_class = e.get("device_class") or e.get("original_device_class")
    if area and domain:
        if domain not in entities_by_area[area]:
            entities_by_area[area][domain] = {"count": 0, "device_classes": {}}
        entities_by_area[area][domain]["count"] += 1
        if dev_class:
            entities_by_area[area][domain]["device_classes"][dev_class] = (
                entities_by_area[area][domain]["device_classes"].get(dev_class, 0) + 1
            )

# Load reference format from contract
contract_path = "canonical/support/contracts/join_contract.yaml"
with open(contract_path) as f:
    contract = yaml.safe_load(f)
ref_format = contract.get("reference_format", {}).get("container_reference", {})
ref_format_keys = ref_format.get("format", ["registry", "id", "name"])


# Compose room_ref and floor_ref in contract-driven format
def container_ref(registry, obj, id_key, name_key):
    ref = {}
    if obj and id_key in obj:
        ref[ref_format_keys[0]] = registry
        ref[ref_format_keys[1]] = obj[id_key]
        ref[ref_format_keys[2]] = obj.get(name_key)
    else:
        ref = {k: None for k in ref_format_keys}
        ref[ref_format_keys[0]] = registry
    return [ref.get(k) for k in ref_format_keys]


CONTRACT_TAG = "alpha_room_registry.output_contract.yaml"


def generate_room_registry():
    alpha_registry = []
    for room in omega_rooms:
        room_id = room.get("id")
        area_tiers = tiers_by_area.get(room_id)
        if not area_tiers or "α" not in area_tiers:
            continue
        floor_obj = next(
            (f for f in floor_registry if room_id in f.get("areas", [])), None
        )
        room_ref = container_ref("core.area_registry", room, "id", "friendly_name")
        floor_ref = container_ref("core.floor_registry", floor_obj, "floor_id", "name")
        room_out = {
            "room_id": room_id,
            "room_ref": room_ref,
            "floor_ref": floor_ref,
            "tier": "α",
            "cluster_size": area_tiers["α"],
            "has_beta": "β" in area_tiers,
            "domains": {},
        }
        if room_out["room_ref"] == [None, None, None]:
            room_out["room_ref"] = None
        if room_out["floor_ref"] == [None, None, None]:
            room_out["floor_ref"] = None
        domain_data = entities_by_area.get(room_id, {})
        for domain, info in domain_data.items():
            domain_entry = {"count": info["count"]}
            if info["device_classes"]:
                domain_entry["device_classes"] = info["device_classes"]
            room_out["domains"][domain] = domain_entry
        alpha_registry.append(room_out)
    alpha_registry.sort(key=lambda x: x["cluster_size"], reverse=True)
    out = {"rooms": alpha_registry}
    # PATCH PIPELINE-FLAGS-V1: Assign only the inner _meta dict for lineage tracking
    out["_meta"] = attach_meta(
        __file__, "PATCH PIPELINE-FLAGS-V1", pipeline_stage="alpha_registry_generation"
    )["_meta"]
    with open("canonical/derived_views/alpha_room_registry.v1.json", "w") as f:
        json.dump(out, f, indent=2)
    print(
        f"✅ Wrote {len(alpha_registry)} alpha-tier rooms to canonical/derived_views/alpha_room_registry.v1.json"
    )


def generate_stub_registry():
    print("Stub for future registry types (e.g., sensor, presence)")


LOG_PATH = Path("canonical/logs/generators/generate_alpha_registry.log")
setup_logging(LOG_PATH)
logging.info("Starting generate_alpha_registry.py run.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Alpha Registry Generator")
    parser.add_argument("--type", choices=["room"], help="Registry type to generate")
    parser.add_argument(
        "--target", choices=["alpha_room_registry"], help="Target registry output"
    )
    args = parser.parse_args()
    if args.type == "room" or args.target == "alpha_room_registry":
        generate_room_registry()
    else:
        generate_stub_registry()
        print("No valid registry type/target specified. Exiting.")
