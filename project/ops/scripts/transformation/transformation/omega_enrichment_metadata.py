#!/usr/bin/env python3
"""
Run as module: python -m scripts.transformation.omega_enrichment_metadata
PATCH-INTEGRATE-ENRICHED-REGISTRY-METADATA-V1
Integrates enriched device metadata subset into the canonical pipeline.
Handles merge, validation, and pipeline metric logging.
"""
import argparse
import datetime
import json

import yaml

# CONTRACT-DRIVEN: Load reference format and conflict resolution from contract
with open("canonical/support/contracts/join_contract.yaml") as f:
    join_contract = yaml.safe_load(f)
ref_format = join_contract.get("reference_format", {}).get("container_reference", {})
conflict_resolution = join_contract.get("conflict_resolution", {})
provenance = join_contract.get("provenance", "unknown")


def load_enriched_subset(path):
    with open(path) as f:
        return json.load(f)


def load_target_registry(path):
    with open(path) as f:
        return json.load(f)


def validate_structural_compliance(enriched, core_registry):
    valid = []
    invalid = []
    core_ids = {d.get("device_id") for d in core_registry}
    for entry in enriched:
        if entry.get("device_id") in core_ids and entry.get("_meta.enrichment"):
            valid.append(entry)
        else:
            invalid.append(entry)
    return valid, invalid


def container_ref(registry, obj, id_key, name_key):
    if obj and id_key in obj and name_key in obj:
        return [
            ref_format.get("format", [registry, obj[id_key], obj[name_key]])[0],
            obj[id_key],
            obj[name_key],
        ]
    elif obj and id_key in obj:
        return [
            ref_format.get("format", [registry, obj[id_key], None])[0],
            obj[id_key],
            None,
        ]
    elif obj and name_key in obj:
        return [
            ref_format.get("format", [registry, None, obj[name_key]])[0],
            None,
            obj[name_key],
        ]
    else:
        return [ref_format.get("format", [registry, None, None])[0], None, None]


def merge_enrichment_into_registry(enriched, core_registry):
    # Conservative merge: only update fields listed in keys_enriched, do not overwrite core fields unless allowed by conflict_resolution
    core_map = {d["device_id"]: d for d in core_registry if "device_id" in d}
    merged = []
    for entry in enriched:
        device_id = entry.get("device_id")
        if device_id in core_map:
            base = core_map[device_id].copy()
            keys = entry.get("_meta.enrichment", {}).get("keys_enriched", [])
            for k in keys:
                if k in entry:
                    # Apply conflict resolution policy
                    override_policy = conflict_resolution.get("enrichment_tiers", [{}])[
                        0
                    ].get("override_policy", "never")
                    if override_policy == "always" or k not in base:
                        base[k] = entry[k]
                    else:
                        # Log conflict if not allowed
                        if base[k] != entry[k]:
                            base.setdefault("enrichment_conflict", []).append(
                                {
                                    "field": k,
                                    "proposed_value": entry[k],
                                    "source": entry.get("_meta", {}).get(
                                        "source", "unknown"
                                    ),
                                }
                            )
            base["_meta.enrichment"] = entry["_meta.enrichment"]
            area_obj = entry.get("area") or base.get("area")
            floor_obj = entry.get("floor") or base.get("floor")
            base["area_ref"] = (
                container_ref("core.area_registry", area_obj, "id", "name")
                if area_obj
                else None
            )
            base["floor_ref"] = (
                container_ref("core.floor_registry", floor_obj, "floor_id", "name")
                if floor_obj
                else None
            )
            base["reference_format"] = ref_format.get("format")
            base["provenance"] = provenance
            if base["area_ref"] == [None, None, None]:
                base["area_ref"] = None
            if base["floor_ref"] == [None, None, None]:
                base["floor_ref"] = None
            merged.append(base)
    return merged


def log_enrichment_metrics_to_pipeline_log(valid, invalid, output_path):
    metrics = {
        "timestamp": datetime.datetime.now().isoformat(),
        "total_enriched": len(valid),
        "invalid_entries": len(invalid),
        "output_path": output_path,
    }
    metrics_path = "canonical/logs/analytics/pipeline_metrics.latest.json"
    try:
        with open(metrics_path, "r") as f:
            logs = json.load(f)
    except Exception:
        logs = []
    logs.append(metrics)
    with open(metrics_path, "w") as f:
        json.dump(logs, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Integrate enriched device metadata into canonical pipeline."
    )
    parser.add_argument(
        "--enriched-path", required=True, help="Path to enriched device registry subset"
    )
    parser.add_argument(
        "--core-path", required=True, help="Path to canonical core device registry"
    )
    parser.add_argument(
        "--target-type",
        default="device",
        choices=["device", "entity", "floor"],
        help="Target registry type",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run validation and metrics only, do not write output",
    )
    parser.add_argument(
        "--output-path",
        default="canonical/derived_views/enriched.device_registry.json",
        help="Output path for merged enriched registry",
    )
    args = parser.parse_args()
    enriched = load_enriched_subset(args.enriched_path)
    core_registry = load_target_registry(args.core_path)
    valid, invalid = validate_structural_compliance(enriched, core_registry)
    merged = merge_enrichment_into_registry(valid, core_registry)
    log_enrichment_metrics_to_pipeline_log(valid, invalid, args.output_path)
    if args.dry_run:
        print(
            f"[DRY RUN] {len(valid)} valid enriched entries, {len(invalid)} invalid. No output written."
        )
    else:
        with open(args.output_path, "w") as f:
            json.dump(merged, f, indent=2)
        print(
            f"[INFO] Merged enriched registry written to {args.output_path} ({len(merged)} entries)"
        )


# PATCH-CONTRACT-CANONICALIZATION-V1: Audit log entry for contract-driven refactor
with open("canonical/logs/scratch/PATCH-CONTRACT-CANONICALIATION-V1.log", "a") as log:
    log.write(
        f"[{datetime.datetime.utcnow().isoformat()}] Refactored omega_enrichment_metadata.py for contract-driven reference format, conflict resolution, and provenance.\n"
    )

if __name__ == "__main__":
    main()
