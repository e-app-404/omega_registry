#!/usr/bin/env python3
"""
Run as module: python -m scripts.generators.generate_flatmap
PATCH ABSOLUTE-IMPORT-UTILS-V1: Refactored for absolute imports, removed sys.path hacks, added run-as-module comment.
"""
"""
PATCH-FLATMAP-MERGE-V1
Unified flatmap generator for entity and device registries.
Replaces generate_entity_flatmap.py and flatten_device_registry.py.
This script consolidates the logic for generating flatmaps for both entities and devices,
allowing for a single entry point with type-based selection.
Usage:
    python generate_flatmap.py --type entity
    python generate_flatmap.py --type device
"""
import argparse
import datetime
import json
import logging
from datetime import datetime
from pathlib import Path

import yaml

from scripts.utils.import_path import set_workspace_root
from scripts.utils.logging import setup_logging

set_workspace_root(__file__)

from scripts.utils.input_list_extract import extract_data
from scripts.utils.logging import attach_meta

# Contract alignment
CONTRACT_PATH = "canonical/support/contracts/join_contract.yaml"
with open(CONTRACT_PATH) as f:
    contract = yaml.safe_load(f)
ref_format = contract.get("reference_format", {}).get("container_reference", {})
ref_format_keys = ref_format.get("format", ["registry", "id", "name"])

LOG_PATH = Path("canonical/logs/generators/generate_flatmap.log")
setup_logging(LOG_PATH)
logging.info("Starting generate_flatmap.py run.")


def load_inference_mappings(contract_path):
    with open(contract_path) as f:
        contract = yaml.safe_load(f)
    return contract.get("inference_mappings", {}).get("rooms", {})


def infer_fields(entity, inference_map):
    area_key = entity.get("area_id")
    device_key = entity.get("device_id")
    info = inference_map.get(area_key) or inference_map.get(device_key) or {}
    entity["tier"] = info.get("tier", entity.get("tier"))
    entity["area_id"] = info.get("area_id", entity.get("area_id"))
    entity["floor_id"] = info.get("floor_id", entity.get("floor_id"))
    entity["platform"] = info.get("platform", entity.get("platform"))
    # Add inference meta
    entity["_meta"] = entity.get("_meta", {})
    entity["_meta"]["inference"] = {
        "source": "join_contract.yaml",
        "timestamp": datetime.now().isoformat(),
    }
    return entity


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


def build_entity_flatmap(entity_registry_path, output_path, metrics_path):
    entities = extract_data(entity_registry_path, load_json(entity_registry_path))
    inference_map = load_inference_mappings(CONTRACT_PATH)
    flatmap = []
    skipped = 0
    for e in entities:
        if not isinstance(e, dict) or not e.get("entity_id"):
            skipped += 1
            continue
        e = infer_fields(e, inference_map)
        entry = {
            "entity_id": e["entity_id"],
            # PATCH-DOMAIN-OVERRIDE-V1: Canonicalize domain from entity_id
            "domain": (
                e["entity_id"].split(".")[0] if e.get("entity_id") else e.get("domain")
            ),
            "tier": e.get("tier"),
            "area_id": e.get("area_id"),
            "floor_id": e.get("floor_id"),
            "platform": e.get("platform"),
            "device_id": e.get("device_id"),
            "disabled": e.get("disabled", False),
            "container_ref": container_ref(
                "core.entity_registry", e, "entity_id", "name"
            ),
            "_meta": e.get("_meta", {}),
        }
        flatmap.append(entry)
    out = {"flatmap": flatmap}
    # PATCH PIPELINE-FLAGS-V1: Assign only the inner _meta dict for lineage tracking
    out["_meta"] = attach_meta(
        __file__, "PATCH PIPELINE-FLAGS-V1", pipeline_stage="flatmap_generation"
    )["_meta"]
    with open(output_path, "w") as f:
        json.dump(out, f, indent=2)
    metrics = {
        "input_count": len(entities),
        "skipped_entries": skipped,
        "output_count": len(flatmap),
        "timestamp": datetime.now().isoformat(),
        "source_file": entity_registry_path,
        "contract": CONTRACT_PATH,
    }
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"✅ Entity flatmap written to {output_path} | Metrics: {metrics_path}")


def build_device_flatmap(device_registry_path, output_path, metrics_path):
    devices = extract_data(device_registry_path, load_json(device_registry_path))
    flatmap = []
    skipped = 0
    for d in devices:
        if not isinstance(d, dict) or not d.get("id"):
            skipped += 1
            continue
        entry = {
            "device_id": d["id"],
            "name": d.get("name"),
            "area_id": d.get("area_id"),
            "disabled": d.get("disabled", False),
            "container_ref": container_ref("core.device_registry", d, "id", "name"),
        }
        flatmap.append(entry)
    out = {"flatmap": flatmap}
    # PATCH PIPELINE-FLAGS-V1: Assign only the inner _meta dict for lineage tracking
    out["_meta"] = attach_meta(
        __file__, "PATCH PIPELINE-FLAGS-V1", pipeline_stage="flatmap_generation"
    )["_meta"]
    with open(output_path, "w") as f:
        json.dump(out, f, indent=2)
    metrics = {
        "input_count": len(devices),
        "skipped_entries": skipped,
        "output_count": len(flatmap),
        "timestamp": datetime.now().isoformat(),
        "source_file": device_registry_path,
        "contract": CONTRACT_PATH,
    }
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"✅ Device flatmap written to {output_path} | Metrics: {metrics_path}")


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Unified Flatmap Generator")
    parser.add_argument(
        "--type",
        required=True,
        choices=["entity", "device"],
        help="Flatmap type to generate",
    )
    args = parser.parse_args()
    if args.type == "entity":
        entity_registry_path = "canonical/registry_inputs/core.entity_registry"
        output_path = "canonical/derived_views/flatmaps/entity_flatmap.json"
        metrics_path = "canonical/logs/analytics/entity_flatmap.metrics.json"
        build_entity_flatmap(entity_registry_path, output_path, metrics_path)
    elif args.type == "device":
        device_registry_path = "canonical/registry_inputs/core.device_registry"
        output_path = "canonical/derived_views/flatmaps/device_flatmap.json"
        metrics_path = "canonical/logs/analytics/device_flatmap.metrics.json"
        build_device_flatmap(device_registry_path, output_path, metrics_path)
    else:
        raise ValueError("Unsupported --type")
