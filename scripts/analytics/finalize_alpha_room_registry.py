#!/usr/bin/env python3
# Run with: python -m scripts.analytics.finalize_alpha_room_registry
"""
PATCH-ALPHA-ROOM-REGISTRY-FINALIZATION-V3
PATCH-CONTRACT-CANONICALIZATION-V1
Finalizes alpha_room_registry with full domain metadata, correct floor_ref, filtering, and logging.
Contract-driven reference format, tier mapping, and cluster threshold enforced.
"""
import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yaml

import scripts.utils.pipeline_config as cfg
from scripts.utils.logging import setup_logging

# Load canonical inputs
with open(str(cfg.ENTITY_FLATMAP)) as f:
    flatmap = json.load(f)["entities"]
with open(str(cfg.PIPELINE_METRICS)) as f:
    metrics = json.load(f)
with open(str(cfg.JOIN_CONTRACT)) as f:
    join_contract = yaml.safe_load(f)
with open("canonical/support/contracts/alpha_room_registry.output_contract.yaml") as f:
    output_contract_raw = yaml.safe_load(f)
if isinstance(output_contract_raw, list):
    output_contract = next(
        (
            item
            for item in output_contract_raw
            if isinstance(item, dict)
            and "tier_mapping_source" in item
            and "cluster_threshold" in item
        ),
        {},
    )
    if not output_contract:
        output_contract = (
            output_contract_raw[-1] if isinstance(output_contract_raw[-1], dict) else {}
        )
else:
    output_contract = output_contract_raw
with open(str(cfg.AREA_HIERARCHY)) as f:
    area_hierarchy = yaml.safe_load(f)
with open(str(cfg.AREA_REGISTRY)) as f:
    area_registry = json.load(f)["data"]["areas"]

# CONTRACT-DRIVEN: Reference format, tier mapping, and cluster threshold
ref_format = join_contract.get("reference_format", {}).get("container_reference", {})
tier_mapping_source = output_contract.get("tier_mapping_source", {})
cluster_threshold = output_contract.get("cluster_threshold", {}).get("min_size", 3)
provenance = join_contract.get("provenance", "unknown")

# Helper: resolve floor_ref for a room
nodes_raw = area_hierarchy.get("nodes", {})
if isinstance(nodes_raw, list):
    nodes = {
        n.get("id") or n.get("room_id"): n
        for n in nodes_raw
        if isinstance(n, dict) and (n.get("id") or n.get("room_id"))
    }
else:
    nodes = nodes_raw
area_by_id = {a["id"]: a for a in area_registry}


def resolve_floor_ref(room_id):
    # CONTRACT-DRIVEN: Use reference format from contract
    node = nodes.get(room_id, {})
    container = node.get("container")
    if isinstance(container, list) and len(container) == 3 and container[0] == "area":
        return [
            ref_format.get("format", ["core.area_registry", "id", "name"])[0],
            container[1],
            container[2],
        ]
    container_id = node.get("container")
    if isinstance(container_id, list):
        container_id = container_id[0] if container_id else None
    if container_id:
        container_node = nodes.get(container_id, {})
        return [
            ref_format.get("format", ["core.floor_registry", "id", "name"])[0],
            container_id,
            container_node.get("friendly_name"),
        ]
    area = area_by_id.get(room_id)
    if area and area.get("floor_id"):
        floor_id = area["floor_id"]
        return [
            ref_format.get("format", ["core.floor_registry", "id", "name"])[0],
            floor_id,
            None,
        ]
    return [None, None, None]


tiers_by_area = metrics.get("tiers_by_area", {})
rooms = [
    room
    for room in tiers_by_area
    if "α" in tiers_by_area[room] and tiers_by_area[room]["α"] > 0
]

output = []
virtual_rooms = []
filtered_rooms = []
floor_issues = []
for room_id in rooms:
    cluster_size = tiers_by_area[room_id]["α"]
    has_beta = "β" in tiers_by_area[room_id]
    # Gather entities for this room
    entities = [
        e for e in flatmap if e.get("area_id") == room_id and e.get("tier") == "α"
    ]
    if not entities:
        filtered_rooms.append(room_id)
        continue
    # Friendly name
    friendly_name = None
    for e in entities:
        if e.get("source_area_ref") and len(e["source_area_ref"]) == 3:
            friendly_name = e["source_area_ref"][2]
            break
    if not friendly_name:
        friendly_name = nodes.get(room_id, {}).get("friendly_name")
    # Floor association
    floor_ref = resolve_floor_ref(room_id)
    meta = {
        "source": "entity_flatmap",
        "reference_format": ref_format.get("format"),
        "provenance": provenance,
    }
    if floor_ref == [None, None, None]:
        meta["missing_floor_ref"] = "true"
        floor_issues.append(room_id)
    # Domain aggregation
    domain_counts = Counter()
    sensor_device_class_counts = defaultdict(Counter)
    for e in entities:
        domain = e.get("domain")
        if domain in ["sensor", "binary_sensor"]:
            device_class = (
                e.get("device_class") or e.get("original_device_class") or "unknown"
            )
            sensor_device_class_counts[domain][device_class] += 1
        else:
            domain_counts[domain] += 1
    # Build domains block, sorted by key
    domains_out = {}
    for domain in sorted(domain_counts.keys()):
        domains_out[domain] = domain_counts[domain]
    for domain in ["sensor", "binary_sensor"]:
        if sensor_device_class_counts[domain]:
            total = sum(sensor_device_class_counts[domain].values())
            domains_out[domain] = {
                "count": total,
                "device_classes": dict(
                    sorted(sensor_device_class_counts[domain].items())
                ),
            }
    # Ensure sensor/binary_sensor domains are present
    for domain in ["sensor", "binary_sensor"]:
        if domain not in domains_out:
            domains_out[domain] = {"count": 0, "device_classes": {}}
    # Output record
    room_entry = {
        "room_id": room_id,
        "friendly_name": friendly_name,
        "floor_ref": floor_ref,
        "tier": "α",
        "cluster_size": cluster_size,
        "has_beta": has_beta,
        "domains": domains_out,
        "_meta": meta,
    }
    if cluster_size < cluster_threshold:
        room_entry["_meta"]["filtered"] = True
        virtual_rooms.append(room_entry)
    else:
        output.append(room_entry)

# Sort by cluster_size descending
output_sorted = sorted(output, key=lambda x: x["cluster_size"], reverse=True)

out_path = "canonical/derived_views/alpha_room_registry.v1.json"
with open(out_path, "w") as f:
    json.dump(output_sorted, f, indent=2)

# Emit summary log
log_path = "canonical/logs/scratch/PATCH-ALPHA-ROOM-REGISTRY-FINALIZATION-V3.log"
Path(log_path).parent.mkdir(parents=True, exist_ok=True)
with open(log_path, "a") as log:
    log.write(
        f"[{datetime.now(timezone.utc).isoformat()}] PATCH-ALPHA-ROOM-REGISTRY-FINALIZATION-V3\n"
    )
    log.write(f"Rooms processed: {len(output_sorted)}\n")
    log.write(f"Virtual rooms (filtered): {len(virtual_rooms)}\n")
    log.write(f"Rooms skipped (no α-tier): {len(filtered_rooms)}\n")
    log.write(f"Floor resolution issues: {floor_issues}\n")
    log.write(f"Output: {out_path}\n")

# PATCH-CONTRACT-CANONICALIZATION-V1: Audit log entry for contract-driven refactor
with open("canonical/logs/scratch/PATCH-CONTRACT-CANONICALIATION-V1.log", "a") as log:
    log.write(
        f"[{datetime.now(timezone.utc).isoformat()}] Refactored finalize_alpha_room_registry.py for contract-driven reference format, tier mapping, and cluster threshold.\n"
    )

LOG_PATH = Path("canonical/logs/analytics/finalize_alpha_room_registry.log")
setup_logging(LOG_PATH)
logging.info("Starting finalize_alpha_room_registry.py run.")

print(
    f"✅ Finalized alpha_room_registry written to {out_path} ({len(output_sorted)} rooms, {len(virtual_rooms)} virtual)"
)
