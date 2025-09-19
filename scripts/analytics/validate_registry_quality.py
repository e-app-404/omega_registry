#!/usr/bin/env python3
# Run with: python -m scripts.analytics.validate_registry_quality
"""
validate_registry_quality.py
QC-REGISTRY-VALIDATION-V1
Automated quality control for canonical registry outputs.
"""
import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from shutil import copy2

import scripts.utils.pipeline_config as cfg
from scripts.utils.logging import setup_logging

LOG_PATH = Path("canonical/logs/analytics/validate_registry_quality.log")
setup_logging(LOG_PATH)

QC_TRACKED_REGISTRIES = {
    "omega": {
        "file": "canonical/derived_views/omega_registry_master.json",
        "qc_metrics": "canonical/logs/governance/omega_registry.qc_metrics.json",
    },
    "alpha_room": {
        "file": "canonical/derived_views/alpha_room_registry.v1.json",
        "qc_metrics": "canonical/logs/governance/alpha_room.qc_metrics.json",
    },
    "alpha_sensor": {
        "file": "canonical/derived_views/alpha_sensor_registry.v1.json",
        "qc_metrics": "canonical/logs/governance/alpha_sensor.qc_metrics.json",
    },
}

HASH_STORE = "canonical/logs/qc/tracked_hashes.json"
BACKUP_DIR = "canonical/logs/governance/qc.backup"
SUMMARY_DIR = "canonical/logs/qc"

REQUIRED_FIELDS = [
    "entity_id",
    "tier",
    "device_class",
    "domain",
    "platform",
    "area_id",
    "floor_id",
    "room_ref",
]


# --- Utility Functions ---
def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def load_json(path):
    with open(path) as f:
        return json.load(f)


def save_json(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)


def field_completeness_score(entity):
    total = len(REQUIRED_FIELDS)
    non_null = sum(
        1 for k in REQUIRED_FIELDS if k in entity and entity[k] not in [None, ""]
    )
    return round(non_null / total, 4) if total else 0.0


def validate_structure(registry):
    if not isinstance(registry, (list, dict)):
        return False, "Registry is not a list or dict"
    entities = registry if isinstance(registry, list) else registry.get("entities", [])
    for e in entities:
        for k in REQUIRED_FIELDS:
            if k not in e:
                return False, f"Missing required field: {k}"
    return True, "Structure valid"


def get_bestof_path(registry_name):
    return f"canonical/logs/governance/{registry_name}_bestof.json"


def rotate_backups(registry_name, new_path):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backups = [f"{BACKUP_DIR}/{registry_name}_v{i}.json" for i in range(1, 4)]
    # Shift backups
    for i in range(2, 0, -1):
        if os.path.exists(backups[i - 1]):
            copy2(backups[i - 1], backups[i])
    copy2(new_path, backups[0])


def main():
    logging.info("Starting validate_registry_quality.py run.")
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate registry quality and promote best-of versions."
    )
    parser.add_argument("--registry", required=True, help="Path to registry JSON")
    parser.add_argument("--reference", required=True, help="Path to best-of JSON")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.01,
        help="Minimum improvement for promotion",
    )
    parser.add_argument(
        "--only-if-changed", action="store_true", help="Skip if hash unchanged"
    )
    parser.add_argument(
        "--hash-store", default=HASH_STORE, help="Path to tracked_hashes.json"
    )
    args = parser.parse_args()

    registry_path = args.registry
    reference_path = args.reference
    registry_name = os.path.basename(registry_path).replace(".json", "")
    now = datetime.now(timezone.utc).isoformat()

    # Load registry and compute hash
    registry = load_json(registry_path)
    latest_sha = compute_sha256(registry_path)

    # Load hash store
    if os.path.exists(args.hash_store):
        tracked_hashes = load_json(args.hash_store)
    else:
        tracked_hashes = {}
    prev_hash = tracked_hashes.get(os.path.basename(registry_path), {}).get("sha256")

    # Only-if-changed logic
    if args.only_if_changed and prev_hash == latest_sha:
        print("[QC] Hash unchanged, skipping validation.")
        sys.exit(0)

    # Validate structure
    structure_valid, structure_msg = validate_structure(registry)
    entities = registry if isinstance(registry, list) else registry.get("entities", [])
    total_entities = len(entities)
    completeness_scores = [field_completeness_score(e) for e in entities]
    completeness_score = (
        round(sum(completeness_scores) / total_entities, 4) if total_entities else 0.0
    )

    # Load reference (best-of)
    # Ensure ref_entities is always defined
    if os.path.exists(reference_path):
        reference = load_json(reference_path)
        ref_entities = (
            reference if isinstance(reference, list) else reference.get("entities", [])
        )
        ref_scores = [field_completeness_score(e) for e in ref_entities]
        previous_score = (
            round(sum(ref_scores) / len(ref_entities), 4) if ref_entities else 0.0
        )
    else:
        ref_entities = []
        previous_score = 0.0

    delta = round(completeness_score - previous_score, 4)
    promote = (
        delta >= args.threshold
        and structure_valid
        and (
            len(ref_entities) == 0
            or abs(total_entities - len(ref_entities))
            / max(total_entities, len(ref_entities))
            < 0.25
        )
    )

    # --- Field Type Validation ---
    FIELD_TYPES = {
        "entity_id": str,
        "tier": str,
        "device_class": str,
        "domain": str,
        "platform": str,
        "area_id": str,
        "floor_id": (str, type(None)),
        "room_ref": (str, type(None)),
    }
    type_errors = []
    for idx, e in enumerate(entities):
        for k, t in FIELD_TYPES.items():
            if k in e and not isinstance(e[k], t):
                type_errors.append(
                    {"index": idx, "field": k, "value": e[k], "expected_type": str(t)}
                )

    # --- Accuracy Checks ---
    # Tier assignment heuristics
    unresolved_tier = sum(
        1 for e in entities if e.get("tier") in [None, "unclassified", "unknown"]
    )
    # Device_class/domain/platform consistency
    inconsistent_device_class = sum(
        1
        for e in entities
        if e.get("device_class")
        and e.get("domain")
        and e.get("device_class") not in ["sensor", "binary_sensor", "switch", "light"]
        and e.get("domain") not in ["sensor", "binary_sensor", "switch", "light"]
    )
    inconsistent_platform = sum(
        1
        for e in entities
        if e.get("platform")
        and e.get("domain")
        and e.get("platform") != e.get("domain")
    )
    # Area/floor/room_ref against area hierarchy
    area_hierarchy_path = str(cfg.AREA_HIERARCHY)
    if os.path.exists(area_hierarchy_path):
        import yaml

        with open(area_hierarchy_path) as f:
            area_hierarchy = yaml.safe_load(f)
        valid_areas = set(n.get("id") for n in area_hierarchy.get("nodes", []))
        invalid_area_refs = sum(
            1
            for e in entities
            if e.get("area_id") and e.get("area_id") not in valid_areas
        )
        invalid_floor_refs = sum(
            1
            for e in entities
            if e.get("floor_id") and e.get("floor_id") not in valid_areas
        )
        invalid_room_refs = sum(
            1
            for e in entities
            if e.get("room_ref") and e.get("room_ref") not in valid_areas
        )
    else:
        invalid_area_refs = invalid_floor_refs = invalid_room_refs = 0

    # --- Warning Triggers ---
    # Cluster size drop > 20%
    cluster_sizes = {}
    for e in entities:
        area = e.get("area_id")
        if area:
            cluster_sizes.setdefault(area, 0)
            cluster_sizes[area] += 1
    ref_cluster_sizes = {}
    for e in ref_entities if "ref_entities" in locals() else []:
        area = e.get("area_id")
        if area:
            ref_cluster_sizes.setdefault(area, 0)
            ref_cluster_sizes[area] += 1
    cluster_drop_warnings = []
    for area, size in cluster_sizes.items():
        ref_size = ref_cluster_sizes.get(area, size)
        if ref_size > 0 and (ref_size - size) / ref_size > 0.2:
            cluster_drop_warnings.append(
                {"area": area, "prev_size": ref_size, "new_size": size}
            )
    # Major field disappearance
    major_fields = ["device_class", "domain", "platform"]
    major_field_missing = {
        f: sum(1 for e in entities if f not in e or e[f] in [None, ""])
        for f in major_fields
    }
    # Content delta < 25%
    content_delta = (
        abs(total_entities - len(ref_entities)) / max(total_entities, len(ref_entities))
        if ref_entities
        else 0.0
    )
    promote = delta >= args.threshold and structure_valid and content_delta < 0.25

    # Backup and promote if improved
    backed_up = False
    reason = ""
    if promote:
        rotate_backups(registry_name, registry_path)
        copy2(registry_path, reference_path)
        backed_up = True
        reason = "Improved completeness, valid schema, within delta range"
    else:
        reason = "No improvement or invalid structure"

    # Update hash store
    tracked_hashes[os.path.basename(registry_path)] = {
        "sha256": latest_sha,
        "last_checked": now,
    }
    save_json(tracked_hashes, args.hash_store)

    # --- Validation Summary ---
    summary = {
        "registry": registry_name,
        "latest_sha": latest_sha,
        "completeness_score": completeness_score,
        "total_entities": total_entities,
        "last_updated": now,
        "previous_score": previous_score,
        "delta": f"{delta:+.4f}",
        "content_delta": round(content_delta, 4),
        "backed_up": backed_up,
        "reason": reason,
        "type_errors": type_errors,
        "unresolved_tier": unresolved_tier,
        "inconsistent_device_class": inconsistent_device_class,
        "inconsistent_platform": inconsistent_platform,
        "invalid_area_refs": invalid_area_refs,
        "invalid_floor_refs": invalid_floor_refs,
        "invalid_room_refs": invalid_room_refs,
        "cluster_drop_warnings": cluster_drop_warnings,
        "major_field_missing": major_field_missing,
    }
    # Emit validation summary
    os.makedirs(SUMMARY_DIR, exist_ok=True)
    summary_path = f"{SUMMARY_DIR}/validation_summary.{registry_name}.json"
    save_json(summary, summary_path)
    print(f"[QC] Validation summary written to {summary_path}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
