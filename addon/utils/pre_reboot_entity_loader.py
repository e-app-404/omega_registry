import json
import time
from pathlib import Path

def slugify(s):
    import re
    return re.sub(r'[^a-zA-Z0-9]+', '_', s.strip().lower()) if s else ''

def derive_canonical_key(entity):
    for k in ("canonical_entity_key", "internal_name", "entity_id", "name"):
        if k in entity and entity[k]:
            return slugify(entity[k])
    return slugify(str(entity))

def load_pre_reboot_entities(paths, return_per_source=False):
    """
    Loads and normalizes all entities from a list of pre-reboot registry files.
    Returns a dict of canonical_entity_key -> entity dict.
    If return_per_source is True, also returns per-source entity counts and lists.
    Patch: Only extract dicts with 'entity_id'. Devices/rooms/areas are counted but not extracted as entities.
    Emits a detailed extraction summary per source.
    """
    pre_entities = {}
    aux_fields_present = {}
    per_source_counts = {}
    per_source_entities = {}
    extraction_summary = []
    canonical_id_issues = []
    canonical_id_stats = {}
    pipeline_trace = []
    all_entities = []
    for path in paths:
        path = Path(path)
        if not path.exists():
            print(f"[WARN] Skipping missing pre-reboot source: {path}")
            continue
        try:
            with open(path) as f:
                try:
                    data = json.load(f)
                except Exception:
                    # Try line-delimited JSON
                    data = [json.loads(line) for line in f if line.strip()]
        except Exception as e:
            print(f"[ERROR] Failed to load {path}: {e}")
            continue
        entities_this_source = []
        skipped_devices = 0
        skipped_areas = 0
        skipped_rooms = 0
        extracted_entity_count = 0
        invalid_keys = []
        # --- Extraction logic ---
        def extract_entities(obj):
            nonlocal skipped_devices, skipped_areas, skipped_rooms, extracted_entity_count
            if isinstance(obj, dict):
                # Entity: must have entity_id
                if "entity_id" in obj:
                    entities_this_source.append(obj)
                    extracted_entity_count += 1
                    for aux in ("original_device_class", "entity_category", "translation_key"):
                        if aux in obj:
                            aux_fields_present[aux] = aux_fields_present.get(aux, 0) + 1
                # Device: skip, but check for nested entities
                elif "entities" in obj and isinstance(obj["entities"], (list, dict)):
                    skipped_devices += 1
                    if isinstance(obj["entities"], list):
                        for ent in obj["entities"]:
                            extract_entities(ent)
                    elif isinstance(obj["entities"], dict):
                        for ent in obj["entities"].values():
                            extract_entities(ent)
                # Room/Area: skip
                elif obj.get("type") == "room" or obj.get("type") == "area" or "area_id" in obj or "room_id" in obj:
                    skipped_rooms += 1
                # Nested dicts: recurse
                else:
                    for v in obj.values():
                        extract_entities(v)
            elif isinstance(obj, list):
                for item in obj:
                    extract_entities(item)
        # Per-source logic
        if isinstance(data, dict):
            if path.name == "omega_device_registry.json":
                devices = data.get("devices", {})
                for dev in devices.values():
                    if "entities" in dev:
                        extract_entities(dev["entities"])
                    else:
                        skipped_devices += 1
            elif path.name == "omega_room_registry.json":
                rooms = data.get("rooms", {})
                for room in rooms.values():
                    if "entities" in room:
                        extract_entities(room["entities"])
                    else:
                        skipped_rooms += 1
            elif path.name == "alpha_sensor_registry.json":
                sensors = data.get("sensors", {})
                for ent in sensors.values():
                    extract_entities(ent)
            elif path.name == "alpha_light_registry.json":
                lights = data.get("lights", {})
                for ent in lights.values():
                    extract_entities(ent)
            elif path.name == "core.entity_registry":
                entities = data.get("data", {}).get("entities", [])
                extract_entities(entities)
            elif path.name == "core.device_registry":
                devs = data.get("data", {}).get("devices", [])
                if isinstance(devs, list):
                    skipped_devices += len(devs)
            elif path.name == "core.area_registry":
                areas = data.get("data", {}).get("areas", [])
                if isinstance(areas, list):
                    skipped_areas += len(areas)
            else:
                extract_entities(data)
                invalid_keys = [k for k in data.keys() if k not in ("sensors", "lights", "rooms", "devices", "data")] if isinstance(data, dict) else []
        elif isinstance(data, list):
            # Fallback: try to extract any dicts with entity_id from the list
            for item in data:
                extract_entities(item)
        per_source_counts[str(path)] = extracted_entity_count
        per_source_entities[str(path)] = entities_this_source
        extraction_summary.append({
            "source_file": str(path),
            "extracted_entity_count": extracted_entity_count,
            "skipped_devices": skipped_devices,
            "skipped_areas": skipped_areas,
            "skipped_rooms": skipped_rooms,
            "invalid_or_ambiguous_keys": invalid_keys,
        })
        # --- Canonical key/canonical_id tracing ---
        with_canonical = 0
        without_canonical = 0
        for ent in entities_this_source:
            canonical_id = None
            # Try known fields for canonical id
            for k in ("canonical_entity_key", "canonical_id", "internal_name", "entity_id", "name"):
                if k in ent and ent[k]:
                    canonical_id = ent[k]
                    break
            if canonical_id:
                with_canonical += 1
            else:
                without_canonical += 1
                canonical_id_issues.append({
                    "entity_id": ent.get("entity_id"),
                    "source": str(path),
                    "issue": "missing canonical_id"
                })
        canonical_id_stats[str(path)] = {
            "with_canonical_id": with_canonical,
            "without_canonical_id": without_canonical
        }
        # After extraction, add all entities to all_entities
        all_entities.extend(entities_this_source)
    # Pipeline trace: initial load
    pipeline_trace.append({"step": "initial_load", "count": len(all_entities)})
    # Example filter: role must be present (if such a filter exists)
    filtered = [e for e in all_entities if isinstance(e, dict)]
    pipeline_trace.append({"step": "after_dict_check", "count": len(filtered), "reason": "must be dict"})
    # Example: filter by entity_id presence
    filtered2 = [e for e in filtered if e.get("entity_id")]
    pipeline_trace.append({"step": "after_entity_id_check", "count": len(filtered2), "reason": "must have entity_id"})
    # Example: filter by is_excluded_entity
    from registry.utils.excluded_registry_entities import is_excluded_entity
    filtered3 = [e for e in filtered2 if not is_excluded_entity(e["entity_id"])]
    pipeline_trace.append({"step": "after_is_excluded_entity", "count": len(filtered3), "reason": "not excluded by is_excluded_entity"})
    # Example: filter by role (if present)
    if any("role" in e for e in filtered3):
        filtered4 = [e for e in filtered3 if e.get("role")]
        pipeline_trace.append({"step": "after_role_filter", "count": len(filtered4), "reason": "role must be present"})
    else:
        filtered4 = filtered3
    # Final: build pre_entities dict
    for ent in filtered4:
        # Use canonical key logic
        for k in ("canonical_entity_key", "canonical_id", "internal_name", "entity_id", "name"):
            if k in ent and ent[k]:
                key = ent[k]
                pre_entities[key] = ent
                break
    pipeline_trace.append({"step": "final_pre_entities", "count": len(pre_entities)})
    # Emit pipeline trace
    with open("output/migration_diagnostics/pre_reboot_entity_pipeline_trace.json", "w") as f:
        json.dump(pipeline_trace, f, indent=2)
    # Emit canonical id issues
    with open("output/migration_diagnostics/pre_reboot_canonical_id_issues.json", "w") as f:
        json.dump(canonical_id_issues, f, indent=2)
    # Print canonical id stats
    print("\n[INFO] Canonical ID tracing per source:")
    for src, stat in canonical_id_stats.items():
        print(f"[INFO] {src}: with_canonical_id={stat['with_canonical_id']}, without_canonical_id={stat['without_canonical_id']}")
    # Emit extraction summary
    ts = time.strftime("%Y%m%dT%H%M%S")
    summary_path = Path(f"data/entity_extraction_summary.{ts}.json")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w") as f:
        json.dump(extraction_summary, f, indent=2)
    if return_per_source:
        return pre_entities, aux_fields_present, per_source_counts, per_source_entities
    return pre_entities, aux_fields_present, {}, {}
