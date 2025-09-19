#!/usr/bin/env python3
"""
Run as module: python -m scripts.transformation.build_enriched_device_map
Builds enriched_device_map.json by merging device_flatmap.json with enrichment log diffs.
Only merges fields that are present in enrichment and missing/null in the source, excluding join keys.
Annotates each device with enrichment metadata for audit and provenance.
"""
import datetime
import json

import yaml

from scripts.utils.logging import attach_meta


def load_json(path):
    with open(path) as f:
        return json.load(f)


def main():
    flatmap_path = "canonical/derived_views/flatmaps/device_flatmap.json"
    enrichment_log_path = (
        "canonical/enrichment_sources/generated/omega_registry_enrichment.log"
    )
    output_path = "canonical/enrichment_sources/generated/enriched_device_map.json"
    flatmap = load_json(flatmap_path)
    with open(enrichment_log_path) as f:
        enrichment_log = json.load(f)
    diffs = enrichment_log.get("diffs", [])
    join_key = enrichment_log.get("field", "mac")
    enrichment_time = enrichment_log.get(
        "timestamp", datetime.datetime.now().isoformat()
    )
    enrichment_source = enrichment_log.get("target", "ip_mac_index.json")
    # Load reference format from contract
    contract_path = "canonical/support/contracts/join_contract.yaml"
    with open(contract_path) as f:
        contract = yaml.safe_load(f)
    ref_format = contract.get("reference_format", {}).get("container_reference", {})
    join_key_fields = ref_format.get("required_fields", [join_key])
    # Use first required field as join key if present in device
    join_key = join_key_fields[1] if len(join_key_fields) > 1 else join_key_fields[0]
    enrichment_lookup = {
        d[join_key]: d
        for d in diffs
        if d["status"] in ["matched", "fallback_matched"] and join_key in d
    }
    enriched_devices = []
    for device in flatmap:
        if not isinstance(device, dict):
            continue  # Skip non-dict entries for robustness
        key = device.get(join_key)
        entry = device.copy()
        enriched_fields = {}  # Always define, so it's safe below
        if key and key in enrichment_lookup:
            diff = enrichment_lookup[key]
            enriched_fields = diff.get("enriched_fields", {})
            # Only merge fields that are present in enrichment and missing/null in source, excluding join key
            for field, value in enriched_fields.items():
                if field == join_key:
                    continue
                if field not in device or device[field] in (None, ""):
                    entry[field] = value
            entry["enrichment_source"] = enrichment_source
            entry["enrichment_confidence"] = enriched_fields.get("confidence")
            entry["join_key_used"] = join_key
            entry["reference_format"] = ref_format.get("format")
            entry["enrichment_time"] = enrichment_time
        # Always emit 'mac' and 'via_device_id' fields at device level
        entry["mac"] = (
            device.get("mac")
            if device.get("mac") is not None
            else (
                enriched_fields.get("mac") if key and key in enrichment_lookup else None
            )
        )
        entry["via_device_id"] = (
            device.get("via_device_id")
            if device.get("via_device_id") is not None
            else (
                enriched_fields.get("via_device_id")
                if key and key in enrichment_lookup
                else None
            )
        )
        enriched_devices.append(entry)
    # When emitting enriched_devices output:
    out = {"devices": enriched_devices}
    out.update(attach_meta(__file__, "enrichment_contract.yaml"))
    with open(
        "canonical/enrichment_sources/generated/enriched_device_map.json", "w"
    ) as f:
        json.dump(out, f, indent=2)
    print(
        f"[INFO] Enriched device map written to {output_path} ({len(enriched_devices)} devices)"
    )


if __name__ == "__main__":
    main()
