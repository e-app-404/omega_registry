import json
import argparse
from pathlib import Path
import os
import sys
import yaml

sys.path.append(str(Path(__file__).parent / "utils"))
from utils.input_list_extract import extract_data
from utils.join_utils import (
    get_device,
    get_area,
    get_floor,
    get_config,
    get_restore,
    is_exposed,
    extract_connection_fields,
)

# Use central path helper to resolve canonical paths
from addon.utils.paths import canonical_path


def load_json(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    # Fallback: try extensionless filename
    if path.endswith(".json"):
        alt_path = path[:-5]
        if os.path.exists(alt_path):
            with open(alt_path) as f:
                return json.load(f)
    print(f"[WARN] Missing input: {path}")
    return None


def load_json_with_extract(path):
    content = load_json(path)
    if content is None:
        return []
    entries = extract_data(path, content)
    if not entries:
        print(f"[WARN] No valid entries extracted from: {path}")
    return entries


def resolve_enrichment_path(subfolder, filename):
    """
    Resolves the canonical path for enrichment sources under enrichment_sources/.
    Example: resolve_enrichment_path('ha_registries/post-reboot', 'core.entity_registry')
    """
    return os.path.join("canonical/enrichment_sources", subfolder, filename)


def main():
    parser = argparse.ArgumentParser(
        description="Generate omega_registry_master.json with debug log support."
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output path for omega_registry_master.json",
    )
    parser.add_argument("--debug_log", help="Path to emit debug .jsonl log")
    args = parser.parse_args()

    # --- BEGIN PATCH: Source Contract Enumeration ---
    contract_path = str(
        canonical_path("support", "contracts", "join_contract.yaml")
    )
    with open(contract_path) as f:
        contract = yaml.safe_load(f)
    expected_files = set()
    file_to_anchor = {}
    for entry in contract["contract"]["sections"]:
        if "canonical_inputs_scope" in entry:
            for fdef in entry["canonical_inputs_scope"]:
                fname = fdef["file"]
                expected_files.add(fname)
        if "files" in entry:
            for fdef in entry["files"]:
                fname = fdef["filename"]
                expected_files.add(fname)
                file_to_anchor[fname] = fdef.get("anchor_type")
    # List of all 15 expected files (from contract)
    all_input_files = list(expected_files)
    # --- END PATCH ---

    # --- BEGIN PATCH: Load all 15 input files ---
    input_dir = str(canonical_path("registry_inputs")) + os.sep
    loaded_files = {}
    for fname in all_input_files:
        fpath_json = os.path.join(input_dir, fname + ".json")
        fpath = (
            fpath_json
            if os.path.exists(fpath_json)
            else os.path.join(input_dir, fname)
        )
        loaded = load_json_with_extract(fpath)
        loaded_files[fname] = loaded
    # --- END PATCH ---

    # Overwrite registry variables with loaded_files for canonical sources
    entity_registry = loaded_files.get("core.entity_registry", [])
    device_registry = loaded_files.get("core.device_registry", [])
    area_registry = loaded_files.get("core.area_registry", [])
    floor_registry = loaded_files.get("core.floor_registry", [])
    config_entries = loaded_files.get("core.config_entries", [])
    restore_state = loaded_files.get("core.restore_state", [])
    exposed_entities = loaded_files.get("homeassistant.exposed_entities", [])

    # Index for fast lookup
    device_by_id = {d["id"]: d for d in device_registry if "id" in d}
    area_by_id = {a["id"]: a for a in area_registry if "id" in a}
    floor_by_id = {f["floor_id"]: f for f in floor_registry if "floor_id" in f}
    config_by_entry = {
        c["entry_id"]: c for c in config_entries if "entry_id" in c
    }
    restore_by_entity = {
        r["entity_id"]: r for r in restore_state if "entity_id" in r
    }
    exposed_set = set(exposed_entities)

    # --- BEGIN PATCH: Enrichment Source Resolution ---
    # All enrichment sources must be loaded from canonical/enrichment_sources/.
    # Example usage: resolve_enrichment_path('ha_registries/post-reboot', 'core.entity_registry')
    # The pipeline should not reference derived_views/.
    # Only scan network/ and manual/ if integration targets exist.
    # --- END PATCH ---

    # --- BEGIN PATCH: Enrichment Source Loading Example ---
    # Example: Load post-reboot entity registry from enrichment_sources
    # Example load of post-reboot entity registry (kept as example; do not assign if unused)
    _ = load_json_with_extract(
        str(
            canonical_path(
                "enrichment_sources",
                "ha_registries",
                "post-reboot",
                "core.entity_registry",
            )
        )
    )
    # Only scan network/ and manual/ if integration targets exist (pseudo-code):
    # if integration_targets:
    #     network_files = os.listdir(resolve_enrichment_path('network', ''))
    #     manual_files = os.listdir(resolve_enrichment_path('manual', ''))
    # --- END PATCH ---

    # --- BEGIN PATCH: Ingestion Status Output ---
    ingestion_status = {
        "expected_files": sorted(list(expected_files)),
        "file_status": {},  # New: detailed extraction outcomes
        "loaded_files": [],
        "missing_files": [],
        "unused_files": [],
    }
    for fname in sorted(list(expected_files)):
        fpath_json = os.path.join(input_dir, fname + ".json")
        fpath = (
            fpath_json
            if os.path.exists(fpath_json)
            else os.path.join(input_dir, fname)
        )
        status = {
            "present": os.path.exists(fpath),
            "extraction": None,
            "reason": None,
        }
        if status["present"]:
            try:
                content = load_json(fpath)
                if content is None:
                    status["extraction"] = False
                    status["reason"] = (
                        "File present but not valid JSON or empty."
                    )
                else:
                    entries = extract_data(fpath, content)
                    if (
                        entries
                        and isinstance(entries, list)
                        and len(entries) > 0
                    ):
                        status["extraction"] = True
                        status["reason"] = f"Extracted {len(entries)} entries."
                        ingestion_status["loaded_files"].append(fname)
                    else:
                        status["extraction"] = False
                        status["reason"] = "No valid entries extracted."
                        ingestion_status["missing_files"].append(fname)
            except Exception as ex:
                status["extraction"] = False
                status["reason"] = f"Extraction error: {ex}"
                ingestion_status["missing_files"].append(fname)
        else:
            status["extraction"] = False
            status["reason"] = "File not found."
            ingestion_status["missing_files"].append(fname)
        ingestion_status["file_status"][fname] = status
    # --- END PATCH ---

    entities = []
    debug_records = []
    enrichment_traces = []
    propagation_audit = []
    used_files = set()
    for e in entity_registry:
        if not isinstance(e, dict):
            print(f"[WARN] Skipped non-dict entity: {repr(e)[:80]}")
            continue
        try:
            join_origin = ["core.entity_registry"]
            field_inheritance = {}
            enrichment_depth = 1
            entity_id = e.get("entity_id")
            device_id = e.get("device_id")
            area_id = e.get("area_id")
            entry_id = e.get("config_entry_id") or e.get("entry_id")
            # Device enrichment
            device = get_device(device_id, device_by_id)
            if device:
                device = extract_connection_fields(
                    device
                )  # PATCH: surface mac/upnp/etc.
                join_origin.append("core.device_registry")
                enrichment_depth += 1
                # Inherit area_id from device if not present
                if not area_id and device.get("area_id"):
                    area_id = device.get("area_id")
                    field_inheritance["area_id"] = "from_device"
            # PATCH: Fallback for device_class from original_device_class
            device_class = e.get("device_class")
            if device_class is None and e.get("original_device_class"):
                device_class = e["original_device_class"]
                field_inheritance["device_class"] = "from_original_device_class"
            else:
                device_class = device_class
            # Area enrichment
            area = get_area(area_id, area_by_id)
            if area:
                join_origin.append("core.area_registry")
                enrichment_depth += 1
                floor_id = area.get("floor_id")
                # Floor enrichment
                floor = get_floor(floor_id, floor_by_id)
                if floor:
                    join_origin.append("core.floor_registry")
                    enrichment_depth += 1
                else:
                    floor = None
            else:
                floor_id = None
                floor = None
            # Config entry enrichment
            config = get_config(entry_id, config_by_entry)
            if config:
                join_origin.append("core.config_entries")
                enrichment_depth += 1
            # Restore state enrichment
            restore = get_restore(entity_id, restore_by_entity)
            if restore:
                join_origin.append("core.restore_state")
                enrichment_depth += 1
            # Exposed entity enrichment
            exposed = is_exposed(entity_id, exposed_set)
            if exposed:
                join_origin.append("homeassistant.exposed_entities")
                enrichment_depth += 1
            # --- BEGIN PATCH: Field Provenance ---
            field_provenance = {}
            # Track provenance for each field in joined entity
            field_provenance["entity_id"] = "core.entity_registry"
            if device_id and device:
                field_provenance["device_id"] = "core.device_registry"
                if device.get("area_id"):
                    field_provenance["area_id"] = (
                        "from_device → core.device_registry"
                    )
            if area_id and area:
                field_provenance["area_id"] = "core.area_registry"
                if area.get("floor_id"):
                    field_provenance["floor_id"] = (
                        "from_area → core.area_registry"
                    )
            if config:
                field_provenance["integration"] = "core.config_entries"
            if restore:
                field_provenance["state_snapshot"] = "core.restore_state"
            if exposed:
                field_provenance["exposed_to_assistant"] = (
                    "homeassistant.exposed_entities"
                )

            # --- END PATCH ---
            # --- BEGIN PATCH: Robust MAC, unique_id, via_device_id propagation and enrichment trace ---
            # MAC extraction: parse device connections for ('mac', ...) tuples
            def extract_mac(device):
                if not device:
                    return None
                # Prefer explicit 'mac' field if present
                if "mac" in device and device["mac"]:
                    return device["mac"]
                # Otherwise, search connections
                for conn in device.get("connections", []):
                    if (
                        isinstance(conn, (list, tuple))
                        and len(conn) == 2
                        and conn[0] == "mac"
                    ):
                        return conn[1]
                return None

            # unique_id propagation: from entity, fallback to device identifiers if possible
            def extract_unique_id(entity, device):
                if entity.get("unique_id"):
                    return entity["unique_id"]
                # Try to infer from device identifiers (e.g., for some integrations)
                if device and "identifiers" in device and device["identifiers"]:
                    # Use the first identifier tuple as a fallback unique_id
                    ident = device["identifiers"][0]
                    if isinstance(ident, (list, tuple)) and len(ident) > 1:
                        return ident[1]
                return None

            # via_device_id propagation: direct and multi-hop
            def resolve_via_device_id(device, device_by_id):
                if not device:
                    return None, []
                path = []
                current = device
                while current and current.get("via_device_id"):
                    path.append(current["id"])
                    next_id = current["via_device_id"]
                    current = device_by_id.get(next_id)
                if path and current:
                    path.append(current["id"])
                return device.get("via_device_id"), path

            mac = extract_mac(device)
            if mac:
                if device and device.get("mac"):
                    field_provenance["mac"] = "core.device_registry:mac"
                else:
                    field_provenance["mac"] = "core.device_registry:connections"
            unique_id = extract_unique_id(e, device)
            if unique_id:
                field_provenance["unique_id"] = (
                    "core.entity_registry"
                    if e.get("unique_id")
                    else "core.device_registry:identifiers"
                )
            via_device_id, via_path = resolve_via_device_id(
                device, device_by_id
            )
            if via_device_id:
                field_provenance["via_device_id"] = "core.device_registry" + (
                    f" (multi-hop: {via_path})" if via_path else ""
                )
            # --- END PATCH ---

            # --- PATCH: Always set mac field in joined entity if found in device connections ---
            # Compose joined entity
            joined = {
                "entity_id": entity_id,
                "unique_id": unique_id,
                "domain": e.get("platform")
                or (entity_id.split(".")[0] if entity_id else None),
                "platform": e.get("platform"),
                "device_class": device_class,
                "entity_category": e.get("entity_category"),
                "name": e.get("name"),
                "original_name": e.get("original_name"),
                "hidden_by": e.get("hidden_by"),
                "disabled_by": e.get("disabled_by"),
                "area_id": area_id,
                "suggested_area": area.get("name") if area else None,
                "floor_id": floor_id if area else None,
                "floor_name": floor.get("name") if floor else None,
                "level": floor.get("level") if floor else None,
                "device_id": device_id,
                "manufacturer": device.get("manufacturer") if device else None,
                "model": device.get("model") if device else None,
                "mac": mac if mac else None,
                "connections": device.get("connections") if device else None,
                "entry_id": entry_id,
                "integration": config.get("domain") if config else None,
                "via_device_id": via_device_id,
                "labels": e.get("labels")
                or (device.get("labels") if device else None),
                "state_snapshot": restore if restore else None,
                "exposed_to_assistant": exposed,
                "join_confidence": None,  # PATCH: Defer confidence until propagation is complete
                "join_origin": join_origin,
                "enrichment_depth": enrichment_depth,
                "field_inheritance": field_inheritance,
                "source": join_origin.copy(),
            }
            # Remove keys with value None for optional fields
            joined = {
                k: v
                for k, v in joined.items()
                if v is not None
                or k
                in [
                    "entity_id",
                    "domain",
                    "platform",
                    "device_class",
                    "entity_category",
                    "name",
                    "area_id",
                    "floor_id",
                    "device_id",
                    "entry_id",
                    "integration",
                    "join_confidence",
                    "join_origin",
                    "enrichment_depth",
                    "field_inheritance",
                ]
            }
            # Only append if entity_id and domain are present
            if joined.get("entity_id") and joined.get("domain"):
                entities.append(joined)
                if args.debug_log:
                    debug_records.append(joined)
                enrichment_traces.append(
                    {
                        "entity_id": entity_id,
                        "joined_from": join_origin,
                        "field_inheritance": field_inheritance,
                        "field_provenance": field_provenance,
                        "mac": mac,
                        "unique_id": unique_id,
                        "via_device_id": via_device_id,
                        "via_device_path": via_path,
                        "missing": [
                            src
                            for src in [
                                "core.config_entries",
                                "core.restore_state",
                                "homeassistant.exposed_entities",
                            ]
                            if src not in join_origin
                        ],
                    }
                )
                propagation_audit.append(
                    {
                        "entity_id": entity_id,
                        "field_provenance": field_provenance,
                    }
                )
                # Track used files
                used_files.update(
                    [src for src in join_origin if src in expected_files]
                )
        except Exception as ex:
            print(f"[WARN] Skipped entity (malformed): {repr(e)[:80]}: {ex}")
            continue
    # --- BEGIN PATCH: Unused Files ---
    unused_files = [
        f for f in loaded_files if f not in used_files and loaded_files[f]
    ]
    ingestion_status["unused_files"] = unused_files
    # --- END PATCH ---
    with open(args.output, "w") as f:
        json.dump(entities, f, indent=2)
    if args.debug_log:
        with open(args.debug_log, "w") as f:
            for rec in debug_records:
                f.write(json.dumps(rec) + "\n")
    # Emit enrichment trace log
    with open(
        str(
            canonical_path(
                "logs", "scratch", "enrichment_trace_omega_registry.jsonl"
            )
        ),
        "w",
    ) as f:
        for trace in enrichment_traces:
            f.write(json.dumps(trace) + "\n")
    # Emit propagation audit trace
    with open(
        str(canonical_path("logs", "scratch", "propagation_audit_trace.jsonl")),
        "w",
    ) as f:
        for rec in propagation_audit:
            f.write(json.dumps(rec) + "\n")
    # Emit source ingestion status
    with open(
        str(
            canonical_path(
                "logs", "scratch", "source_file_ingestion_status.json"
            )
        ),
        "w",
    ) as f:
        json.dump(ingestion_status, f, indent=2)
    # Emit unused sources log
    with open(
        str(
            canonical_path(
                "logs", "scratch", "omega_registry_unused_sources.log"
            )
        ),
        "w",
    ) as f:
        for fname in unused_files:
            f.write(f"Unused input file: {fname}\n")
    print(f"[INFO] Emitted omega_registry_master.json: {args.output}")
    if args.debug_log:
        print(f"[INFO] Emitted debug log: {args.debug_log}")
    print(
        f"[INFO] Emitted enrichment trace log: {str(canonical_path('logs', 'scratch', 'enrichment_trace_omega_registry.jsonl'))}"
    )
    print(
        f"[INFO] Emitted propagation audit trace: {str(canonical_path('logs', 'scratch', 'propagation_audit_trace.jsonl'))}"
    )
    print(
        f"[INFO] Emitted source ingestion status: {str(canonical_path('logs', 'scratch', 'source_file_ingestion_status.json'))}"
    )
    print(
        f"[INFO] Emitted unused sources log: {str(canonical_path('logs', 'scratch', 'omega_registry_unused_sources.log'))}"
    )


if __name__ == "__main__":
    main()
