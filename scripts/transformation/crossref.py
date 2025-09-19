#!/usr/bin/env python3
"""
Run as module: python -m scripts.transformation.crossref
PATCH-XREF-ENRICHMENT-IMPLICATIONS-V1
PATCH-CONTRACT-CANONICALIZATION-V1

Cross-references two registries by a field and emits enrichment audit logs. Accepts device_flatmap.json as a source for device-level enrichment.

Implements target-driven analytics, enrichment implication annotation, and structured summary block.
Contract-driven reference format, required fields, and provenance logic enforced.
"""

import argparse
import datetime
import json
import logging
from pathlib import Path

import yaml

from scripts.utils.input_list_extract import extract_data
from scripts.utils.logging import setup_logging

LOG_PATH = Path("canonical/logs/transformation/crossref.log")
setup_logging(LOG_PATH)
logging.info("Starting crossref.py run.")


def load_json(path):
    with open(path) as f:
        return json.load(f)


def is_flatmap(path):
    return path.endswith("device_flatmap.json")


def main():
    parser = argparse.ArgumentParser(
        description="Cross-reference two registries by a field and emit enrichment audit log."
    )
    parser.add_argument(
        "--source", required=True, help="Path to source JSON (to be enriched)"
    )
    parser.add_argument("--target", required=True, help="Path to target JSON (lookup)")
    parser.add_argument("--field", required=True, help="Field to match on (e.g., mac)")
    parser.add_argument(
        "--append", nargs="+", required=True, help="Fields from target to append"
    )
    parser.add_argument(
        "--log", required=True, help="Path to audit log output (.json or .yaml)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview matches without writing log"
    )
    parser.add_argument(
        "--fallback-fields",
        nargs="*",
        default=[],
        help="Secondary fields to try if primary match fails",
    )
    parser.add_argument(
        "--source-filter",
        type=str,
        default=None,
        help="Optional lambda filter for source entries",
    )
    args = parser.parse_args()

    source_content = load_json(args.source)
    if is_flatmap(args.source):
        source = (
            source_content["flatmap"]
            if isinstance(source_content, dict) and "flatmap" in source_content
            else source_content
        )
        print(f"[INFO] Using device_flatmap.json as source, {len(source)} entries.")
    else:
        source = extract_data(args.source, source_content)
    target_content = load_json(args.target)
    target_entries = extract_data(args.target, target_content)

    # CONTRACT-DRIVEN: Load reference format, required fields, and provenance from contract
    contract_path = "canonical/support/contracts/join_contract.yaml"
    with open(contract_path) as f:
        contract = yaml.safe_load(f)
    ref_format = contract.get("reference_format", {}).get("container_reference", {})
    match_fields = ref_format.get("required_fields", [args.field])
    provenance = contract.get("provenance", "unknown")
    # Use first required field as match field if present in source
    primary_field = match_fields[1] if len(match_fields) > 1 else match_fields[0]
    lookups = {
        primary_field: {
            entry.get(primary_field): entry
            for entry in target_entries
            if entry.get(primary_field)
        }
    }
    for f in args.fallback_fields:
        lookups[f] = {entry.get(f): entry for entry in target_entries if entry.get(f)}

    # Optional source filtering
    if args.source_filter:
        try:
            source = [e for e in source if eval(args.source_filter)]
        except Exception as ex:
            print(f"[WARN] Source filter eval failed: {ex}")

    audit_log = []
    for idx, entry in enumerate(source):
        if not isinstance(entry, dict):
            print(
                f"[WARN] Skipping non-dict entry at index {idx} in source: {repr(entry)[:80]}"
            )
            continue
        match = None
        match_field = None
        match_value = None
        status = "unmatched"
        # Try primary field
        key = entry.get(primary_field)
        if key and key in lookups[primary_field]:
            match = lookups[primary_field][key]
            match_field = primary_field
            match_value = key
            status = "matched"
        else:
            # Try fallback fields
            for f in args.fallback_fields:
                key_f = entry.get(f)
                if key_f and key_f in lookups[f]:
                    match = lookups[f][key_f]
                    match_field = f
                    match_value = key_f
                    status = "fallback_matched"
                    break
        enriched_fields = {}
        if match:
            name = match.get("name_by_user") or match.get("name")
            enriched_fields["hostname"] = name
            enriched_fields["device_id"] = match.get("id")
            for af in args.append:
                enriched_fields[af] = match.get(af)
        audit_entry = {
            "source_index": idx,
            "match_field": match_field,
            "match_value": match_value,
            "status": status,
            "reference_format": ref_format.get("format"),
            "required_fields": match_fields,
            "provenance": provenance,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        audit_log.append(audit_entry)

    # PATCH-XREF-ENRICHMENT-IMPLICATIONS-V1: Target-driven analytics and enrichment implication annotation
    enrichment_subject_type = (
        "device" if "device" in args.source or "flatmap" in args.source else "entity"
    )
    crossref_type = "enrichment"
    enrichment_fields_transferred = [f for f in args.append]
    target_entries_scanned = len(target_entries)
    target_entries_enriched = 0
    target_entries_unenriched = 0
    overmatches_detected = 0
    diffs = []
    for t_entry in target_entries:
        match = None
        match_field = None
        match_value = None
        status = "unmatched"
        enrichment_potential = {
            "transfer_mac": "mac" in args.append,
            "transfer_ipv4": "ipv4" in args.append,
            "attach_device_tracker": True,
            "attach_hostname": "hostname" in args.append,
        }
        # Try primary field
        key = t_entry.get(args.field)
        if key and key in lookups[args.field]:
            match = lookups[args.field][key]
            match_field = args.field
            match_value = key
            status = "matched"
        else:
            # Try fallback fields
            for f in args.fallback_fields:
                key_f = t_entry.get(f)
                if key_f and key_f in lookups[f]:
                    match = lookups[f][key_f]
                    match_field = f
                    match_value = key_f
                    status = "fallback_matched"
                    break
        enriched_fields = {}
        if match:
            enrichment_potential["attach_device_tracker"] = True
            enrichment_potential["transfer_mac"] = bool(match.get("mac"))
            enrichment_potential["transfer_ipv4"] = bool(match.get("ipv4"))
            enrichment_potential["attach_hostname"] = bool(match.get("hostname"))
            for af in args.append:
                enriched_fields[af] = match.get(af)
            target_entries_enriched += 1
        else:
            target_entries_unenriched += 1
        diffs.append(
            {
                "target_id": t_entry.get("entity_id") or t_entry.get("id"),
                "match_field": match_field,
                "match_value": match_value,
                "enriched_fields": enriched_fields,
                "status": status,
                "enrichment_potential": enrichment_potential,
            }
        )
    if target_entries_enriched > target_entries_scanned:
        overmatches_detected = target_entries_enriched - target_entries_scanned
    match_rate_percent = (
        (target_entries_enriched / target_entries_scanned * 100)
        if target_entries_scanned
        else 0.0
    )
    summary = {
        "crossref_type": crossref_type,
        "enrichment_subject_type": enrichment_subject_type,
        "target_entries_scanned": target_entries_scanned,
        "target_entries_enriched": target_entries_enriched,
        "target_entries_unenriched": target_entries_unenriched,
        "match_rate_percent": round(match_rate_percent, 2),
        "overmatches_detected": overmatches_detected,
        "enrichment_fields_transferred": enrichment_fields_transferred,
    }
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "source": args.source,
        "target": args.target,
        "field": args.field,
        "fallback_fields": args.fallback_fields,
        "append_fields": args.append,
        "dry_run": args.dry_run,
        "summary": summary,
        "diffs": diffs,
    }
    # PATCH-XREF-ENRICHMENT-IMPLICATIONS-V1: Emit full structured log in both dry-run and normal mode
    if args.dry_run:
        print(yaml.dump(log_entry, sort_keys=False))
    else:
        with open(args.log, "w") as f:
            if args.log.endswith(".yaml"):
                yaml.dump(log_entry, f, sort_keys=False)
            else:
                json.dump(log_entry, f, indent=2)


if __name__ == "__main__":
    main()
# PATCH-XREF-ENRICHMENT-IMPLICATIONS-V1 END
