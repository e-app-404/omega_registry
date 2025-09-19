#!/usr/bin/env python3
"""
Run as module: python -m scripts.transformation.refine_enriched_device_registry
PATCH-ENRICHED-DEVICE-REGISTRY-V2
Emits only enriched entries to enriched_device_registry_subset.json, with metadata under _meta.
Skips entries with empty enrichment or null match_value. No top-level pollution. Contract-compliant.
"""
import argparse
import datetime
import json

import yaml

from scripts.utils.logging import attach_meta
from scripts.utils.pipeline_config import (
    DEVICE_TRACKER_ENTITY_TYPE,
    ENRICHED_DEVICE_MAP_PATH,
    ENRICHED_DEVICE_OUTPUT_FIELDS,
    ENRICHMENT_FIELD_LIST,
    ENRICHMENT_LOG_PATH,
    ENRICHMENT_TARGET_PATHS,
    REGISTRY_SOURCE_FILES,
    SOURCE_REGISTRY,
    VALID_ANCHOR_TYPES,
)


def load_json(path):
    with open(path) as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Emit enriched device registry subset with contract metadata."
    )
    parser.add_argument(
        "--contract_tag", help="Contract audit tag for enrichment metadata"
    )
    parser.add_argument(
        "--anchor_type",
        required=True,
        choices=VALID_ANCHOR_TYPES,
        help="Anchor type being enriched (e.g., device_registry, entity_registry)",
    )
    args = parser.parse_args()
    if not args.contract_tag:
        print("[ERROR] --contract_tag argument is required. Example usage:")
        print(
            "  python3 scripts/refine_enriched_device_registry.py --contract_tag PATCH-ENRICHMENT-DEVICE-TRACKER-LINK-V1 --anchor_type device_registry"
        )
        return
    if not args.anchor_type:
        print("[ERROR] --anchor_type argument is required. Example usage:")
        print(
            "  python3 scripts/refine_enriched_device_registry.py --contract_tag PATCH-ENRICHMENT-DEVICE-TRACKER-LINK-V1 --anchor_type device_registry"
        )
        return
    input_path = ENRICHED_DEVICE_MAP_PATH
    output_path = ENRICHMENT_TARGET_PATHS.get(
        args.anchor_type,
        f"canonical/enrichment_sources/generated/enriched_{args.anchor_type}_subset.json",
    )
    contract_tag = args.contract_tag
    now = datetime.datetime.now().isoformat()
    source_registry = SOURCE_REGISTRY
    REGISTRY_SOURCE_FILES.get(
        args.anchor_type, "core.device_registry"
    )
    devices = load_json(input_path)
    enrichment_log_path = ENRICHMENT_LOG_PATH
    enrichment_log = load_json(enrichment_log_path)
    tracker_lookup = {
        d["match_value"]: d["target_id"]
        for d in enrichment_log.get("diffs", [])
        if d["status"] in ["matched", "fallback_matched"]
    }
    with open("canonical/support/contracts/join_contract.yaml") as f:
        join_contract = yaml.safe_load(f)
    ref_format = join_contract.get("reference_format", {}).get(
        "container_reference", {}
    )
    provenance = join_contract.get("provenance", "unknown")
    subset = []
    for entry in devices:
        match_key = entry.get("join_key_used", "mac")
        match_value = entry.get(match_key)
        enrichment_fields = {}
        for k in ENRICHMENT_FIELD_LIST:
            v = entry.get(k)
            if v not in (None, ""):
                enrichment_fields[k] = v
        if match_value and enrichment_fields:
            out = {k: entry[k] for k in entry if k in ENRICHED_DEVICE_OUTPUT_FIELDS}
            out.update(enrichment_fields)
            linked_entity = tracker_lookup.get(match_value)
            if linked_entity and linked_entity != entry.get("device_id"):
                out["linked_entity"] = linked_entity
                out["linked_entity_type"] = DEVICE_TRACKER_ENTITY_TYPE
            out["reference_format"] = ref_format.get("format")
            out["provenance"] = provenance
            out["_meta.enrichment"] = {
                "match": [match_key, match_value],
                "confidence": entry.get("confidence", 1.0),
                "keys_enriched": list(enrichment_fields.keys())
                + (["linked_entity"] if "linked_entity" in out else []),
                "contract": {
                    "generated_by": ["crossref.py", source_registry],
                    "timestamp": now,
                    "audit_tag": contract_tag,
                },
            }
            out.pop("_meta", None)
            subset.append(out)
    out = {"devices": subset}
    out.update(attach_meta(__file__, "enrichment_contract.yaml"))
    with open(
        "canonical/enrichment_sources/generated/enriched_device_registry_subset.json",
        "w",
    ) as f:
        json.dump(out, f, indent=2)
    print(
        f"[INFO] Enriched device registry subset written to {output_path} ({len(subset)} enriched devices)"
    )
    # PATCH-CONTRACT-CANONICALIZATION-V1: Audit log entry for contract-driven refactor
    with open(
        "canonical/logs/scratch/PATCH-CONTRACT-CANONICALIATION-V1.log", "a"
    ) as log:
        log.write(
            f"[{now}] Refactored refine_enriched_device_registry.py for contract-driven reference format and provenance.\n"
        )


if __name__ == "__main__":
    main()
