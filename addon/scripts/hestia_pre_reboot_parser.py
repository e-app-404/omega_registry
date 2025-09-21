import os
import json
from pathlib import Path
from collections import defaultdict
import yaml
from addon.utils.paths import canonical_path

# PATCH: Output contract path updated for new location
OUTPUT_CONTRACT_PATH = str(
    canonical_path(
        "support", "contracts", "hestia_pre_reboot_parser.output_contract.yaml"
    )
)


def parse_legacy_hestia_registries(
    input_dir, output_summary_path, debug_log=None
):
    """
    Parse legacy Hestia pre-reboot registries and emit a structured enrichment summary.
    """
    files = list(Path(input_dir).glob("*.json"))
    field_stats = defaultdict(
        lambda: {
            "source_files": set(),
            "value_types": set(),
            "occurrences": 0,
            "example_values": set(),
        }
    )
    canonical_fields = set()  # Optionally load from canonical schema
    debug_entries = []
    for file in files:
        file_debug = {
            "filename": str(file),
            "entry_count": 0,
            "sample_entries": [],
            "skipped": [],
            "malformed": [],
        }
        with open(file) as f:
            try:
                data = json.load(f)
            except Exception as e:
                file_debug["malformed"].append(
                    {"error": "invalid json", "exception": str(e)}
                )
                debug_entries.append(file_debug)
                continue
        # Support both list and dict root
        # Correct entry extraction logic for legacy HESTIA registries
        if isinstance(data, list):
            entries = data
        elif (
            isinstance(data, dict)
            and "data" in data
            and "entities" in data["data"]
        ):
            entries = data["data"]["entities"]
        elif isinstance(data, dict):
            entries = list(
                data.values()
            )  # fallback, in case it's a dict of entity_id: entity_obj
        else:
            entries = []
        print(f"[DEBUG] Parsed {len(entries)} entries from {file.name}")
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                file_debug["skipped"].append({"reason": "not a dict"})
                continue
            for k, v in entry.items():
                # Use local variables for accumulation
                local_source_files = set()
                local_value_types = set()
                local_occurrences = 0
                local_example_values = set()
                # If field_stats[k] is a dict, accumulate existing values
                if isinstance(field_stats[k], dict):
                    sf = field_stats[k].get("source_files")
                    if isinstance(sf, set):
                        local_source_files = set(sf)
                    vt = field_stats[k].get("value_types")
                    if isinstance(vt, set):
                        local_value_types = set(vt)
                    occ = field_stats[k].get("occurrences")
                    if isinstance(occ, int):
                        local_occurrences = occ
                    ev = field_stats[k].get("example_values")
                    if isinstance(ev, set):
                        local_example_values = set(ev)
                # Accumulate
                local_source_files.add(str(file))
                local_value_types.add(type(v).__name__)
                local_occurrences += 1
                if len(local_example_values) < 5:
                    local_example_values.add(str(v))
                # Assign back to field_stats[k]
                field_stats[k] = {
                    "source_files": local_source_files,
                    "value_types": local_value_types,
                    "occurrences": local_occurrences,
                    "example_values": local_example_values,
                }
        file_debug["entry_count"] = len(entries)
        debug_entries.append(file_debug)
    # Prepare summary
    summary = []
    for field, stats in field_stats.items():
        # Defensive: ensure correct types for summary output
        source_files = (
            stats["source_files"]
            if isinstance(stats["source_files"], set)
            else set()
        )
        value_types = (
            stats["value_types"]
            if isinstance(stats["value_types"], set)
            else set()
        )
        example_values = (
            stats["example_values"]
            if isinstance(stats["example_values"], set)
            else set()
        )
        summary.append(
            {
                "field_name": field,
                "source_files": sorted(list(source_files)),
                "value_types": sorted(list(value_types)),
                "occurrences": stats["occurrences"]
                if isinstance(stats["occurrences"], int)
                else 0,
                "example_values": sorted(list(example_values)),
                "match_to": "canonical"
                if field in canonical_fields
                else "non-canonical",
            }
        )
    with open(output_summary_path, "w") as f:
        yaml.dump({"fields": summary}, f)
    print(f"[INFO] Emitted enrichment summary: {output_summary_path}")
    if debug_log:
        with open(debug_log, "w") as f:
            for entry in debug_entries:
                f.write(json.dumps(entry) + "\n")
    # Log patch execution
    with open("PATCH-ROUNDTRIP-AUDIT-V2.log", "a") as audit:
        audit.write(
            "[PATCH-ACTIVE: DEBUG_LOGGER_EXTENSION_V1] Ran parse_legacy_hestia_registries with debug_log=%s\n"
            % (debug_log or "None")
        )


def extract_hestia_pre_reboot_insights(
    input_dir, out_map, out_hints, out_diag, out_drift, debug_log=None
):
    """
    Integrate pre-reboot Hestia registries into canonical join graph and emit required outputs.
    PATCH-ACTIVE: HESTIA_JOIN_GRAPH_FIX_V2
    """
    import re

    files = sorted(
        Path(input_dir).glob("*.json"),
        key=lambda f: (re.search(r"(\\d{2}-\\d{2})", f.name), f.name),
        reverse=True,
    )
    field_map = defaultdict(set)
    join_hints = []
    diagnostics = []
    schema_drift = []
    debug_entries = []
    entity_by_id = {}
    entity_file_info = {}
    joinable_fields = [
        "area_id",
        "device_id",
        "mac",
        "name",
        "platform",
        "domain",
        "device_class",
    ]
    required_fields = {"id", "area_id", "name"}
    file_entity_ids = {}
    for file in files:
        file_debug = {
            "filename": str(file),
            "entry_count": 0,
            "valid_entries": 0,
            "skipped": [],
            "malformed": [],
            "conflicts": [],
            "missing_required": [],
            "collisions": [],
            "sample_entries": [],
        }
        with open(file) as f:
            try:
                data = json.load(f)
            except Exception as e:
                diagnostics.append(
                    {
                        "file": str(file),
                        "error": "invalid json",
                        "exception": str(e),
                    }
                )
                file_debug["malformed"].append(
                    {"error": "invalid json", "exception": str(e)}
                )
                debug_entries.append(file_debug)
                continue

        # RECURSIVE PATCH: Find all dicts with 'id' at any depth
        def recursive_entity_search(obj, found, line_hint=None):
            if isinstance(obj, dict):
                if "id" in obj:
                    found.append((obj, line_hint))
                for k, v in obj.items():
                    recursive_entity_search(v, found, line_hint)
            elif isinstance(obj, list):
                for item in obj:
                    recursive_entity_search(item, found, line_hint)

        all_entity_dicts = []
        recursive_entity_search(data, all_entity_dicts)
        file_entity_ids[str(file)] = set()
        for i, (entry, line_hint) in enumerate(all_entity_dicts):
            eid = entry.get("id")
            if eid is None:
                file_debug["skipped"].append(
                    {"reason": "missing id", "entry": entry}
                )
                continue
            file_entity_ids[str(file)].add(eid)
            # Deduplication: prefer most recent file version
            if eid in entity_by_id:
                # Collision/conflict detection
                prev = entity_by_id[eid]
                if prev != entry:
                    file_debug["collisions"].append(
                        {
                            "entity_id": eid,
                            "prev_file": entity_file_info[eid]["file"],
                            "curr_file": str(file),
                        }
                    )
            entity_by_id[eid] = entry
            entity_file_info[eid] = {"file": str(file), "line": line_hint}
            # Join field extraction
            join_fields = {k: entry[k] for k in joinable_fields if k in entry}
            join_hint = {"entity_id": eid, "join_fields": join_fields}
            join_hints.append(join_hint)
            # Field map
            for k, v in entry.items():
                field_map[k].add(type(v).__name__)
            # Schema drift
            missing = required_fields - set(entry.keys())
            unexpected = (
                set(entry.keys()) - required_fields - set(joinable_fields)
            )
            drift = {"entity_id": eid, "source_file": str(file)}
            if missing:
                drift["missing_fields"] = list(missing)
            if unexpected:
                drift["unexpected_fields"] = list(unexpected)
            if drift.keys() - {"entity_id", "source_file"}:
                if line_hint is not None:
                    drift["source_line"] = line_hint
                schema_drift.append(drift)
            # Diagnostics
            if missing:
                file_debug["missing_required"].append(
                    {"entity_id": eid, "missing": list(missing)}
                )
            file_debug["valid_entries"] += 1
            if len(file_debug["sample_entries"]) < 2:
                file_debug["sample_entries"].append(
                    {
                        "keys": list(entry.keys()),
                        "types": {
                            k: type(v).__name__ for k, v in entry.items()
                        },
                    }
                )
        file_debug["entry_count"] = len(all_entity_dicts)
        debug_entries.append(file_debug)
    # Emit outputs
    with open(out_map, "w") as f:
        json.dump(
            {k: sorted(list(v)) for k, v in field_map.items()}, f, indent=2
        )
    with open(out_hints, "w") as f:
        json.dump(
            list(
                entity_by_id[eid]
                and {
                    "entity_id": eid,
                    "join_fields": {
                        k: entity_by_id[eid][k]
                        for k in joinable_fields
                        if k in entity_by_id[eid]
                    },
                }
                for eid in entity_by_id
            ),
            f,
            indent=2,
        )
    with open(out_diag, "w") as f:
        for entry in debug_entries:
            f.write(json.dumps(entry) + "\n")
    with open(out_drift, "w") as f:
        json.dump(schema_drift, f, indent=2)
    if debug_log:
        with open(debug_log, "w") as f:
            for entry in debug_entries:
                f.write(json.dumps(entry) + "\n")
    # Log patch execution
    with open("PATCH-ROUNDTRIP-AUDIT-V2.log", "a") as audit:
        audit.write(
            "[PATCH-ACTIVE: HESTIA_JOIN_GRAPH_FIX_V2] Ran extract_hestia_pre_reboot_insights with deduplication, join field extraction, schema drift enrichment, and enhanced diagnostics. debug_log=%s\n"
            % (debug_log or "None")
        )
    with open(
        str(canonical_path("logs", "copilot_patchlog.log")), "a"
    ) as patchlog:
        patchlog.write(
            "[PATCH: HESTIA_JOIN_GRAPH_FIX_V2] join_hints now emit deduped, rich join_fields per entity. %s\n"
            % (debug_log or "")
        )
    print(f"[INFO] Emitted field map: {out_map}")
    print(f"[INFO] Emitted join hints: {out_hints}")
    print(f"[INFO] Emitted diagnostics: {out_diag}")
    print(f"[INFO] Emitted schema drift: {out_drift}")
    if debug_log:
        print(f"[INFO] Emitted debug log: {debug_log}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Hestia Pre-Reboot Registry Analysis (now with --debug_log for .jsonl diagnostics)"
    )
    parser.add_argument(
        "--mode", choices=["enrichment_summary", "join_graph"], required=True
    )
    parser.add_argument(
        "--input_dir",
        default=str(
            canonical_path("derived_views", "hestia_registries", "pre-reboot")
        )
        + os.sep,
        help="Input directory of legacy registries",
    )
    parser.add_argument("--output", help="Output file (for enrichment summary)")
    parser.add_argument("--out_map", help="Field map output (for join graph)")
    parser.add_argument(
        "--out_hints", help="Join hints output (for join graph)"
    )
    parser.add_argument(
        "--out_diag", help="Diagnostics log output (for join graph)"
    )
    parser.add_argument(
        "--out_drift", help="Schema drift output (for join graph)"
    )
    parser.add_argument(
        "--debug_log",
        help="Emit .jsonl debug log of all parsed files and entries (for both modes)",
    )
    args = parser.parse_args()
    if args.mode == "enrichment_summary":
        output = args.output or str(
            canonical_path(
                "diagnostics", "legacy_registry_enrichment_summary.yaml"
            )
        )
        parse_legacy_hestia_registries(
            args.input_dir, output, debug_log=args.debug_log
        )
    elif args.mode == "join_graph":
        extract_hestia_pre_reboot_insights(
            args.input_dir,
            args.out_map
            or str(canonical_path("logs", "hestia_pre_reboot_field_map.json")),
            args.out_hints
            or str(canonical_path("joins", "pre_reboot_field_join_hints.json")),
            args.out_diag
            or str(
                canonical_path(
                    "logs", "hestia_pre_reboot_field_diagnostics.log"
                )
            ),
            args.out_drift
            or str(
                canonical_path("logs", "hestia_pre_reboot_schema_drift.json")
            ),
            args.debug_log,
        )
