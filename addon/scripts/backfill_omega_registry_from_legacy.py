import json
import os
from datetime import datetime
from collections import defaultdict
from copy import deepcopy
import yaml # type: ignore
from registry.utils.synonyms import FIELD_SYNONYMS

# --- CONFIGURATION ---
settings_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../settings.conf.yaml'))
with open(settings_path, "r") as f:
    settings_yaml = yaml.safe_load(f)
settings = settings_yaml["settings"]
OMEGA_PATH = settings["output_paths"]["omega_enriched_devtools"]
LEGACY_PATHS = {
    "alpha_light": settings["input_paths"].get("legacy_alpha_light", "input/pre-reboot.hestia_registries/alpha_light_registry.json"),
    "alpha_sensor": settings["input_paths"].get("legacy_alpha_sensor", "input/pre-reboot.hestia_registries/alpha_sensor_registry.json"),
    "alpha_system": settings["input_paths"].get("legacy_alpha_system", "input/pre-reboot.hestia_registries/alpha_system_registry.json"),
    "device_groups": settings["input_paths"].get("legacy_device_groups", "input/pre-reboot.hestia_registries/device_groups.json"),
    "omega_room": settings["input_paths"].get("legacy_omega_room", "input/pre-reboot.hestia_registries/omega_room_registry.json")
}
REPORT_PATH = f"output/data/backfill_omega_registry_report_{datetime.now().strftime('%Y%m%d_%H%M')}.log"

# FIELD_MAPPING moved to utils/synonyms.py as FIELD_SYNONYMS

# --- UTILS ---
def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def normalize_key(val):
    if isinstance(val, str):
        return val.lower().replace("-", "_").replace(" ", "_")
    return str(val)

def all_possible_ids(device):
    ids = set()
    for k in ("id", "name", "internal_name", "canonical_id"):
        v = device.get(k)
        if v:
            ids.add(normalize_key(v))
    for ident in device.get("identifiers", []):
        if isinstance(ident, (list, tuple)):
            for i in ident:
                ids.add(normalize_key(i))
        else:
            ids.add(normalize_key(ident))
    return ids

def flatten_legacy_devices(legacy, source_file):
    # Returns list of (device_dict, source_file)
    out = []
    if not legacy:
        return out
    if "devices" in legacy:
        for d in legacy["devices"]:
            d = deepcopy(d)
            d["_source_file"] = source_file
            out.append(d)
    elif "light_devices" in legacy:
        light_devices = legacy["light_devices"]
        if isinstance(light_devices, dict):
            for k, d in light_devices.items():
                d = deepcopy(d)
                d["_source_file"] = source_file
                d["id"] = d.get("id", k)
                out.append(d)
        elif isinstance(light_devices, list):
            for d in light_devices:
                d = deepcopy(d)
                d["_source_file"] = source_file
                out.append(d)
    elif "sensors" in legacy:
        sensors = legacy["sensors"]
        if isinstance(sensors, dict):
            for k, d in sensors.items():
                d = deepcopy(d)
                d["_source_file"] = source_file
                d["id"] = d.get("id", k)
                out.append(d)
        elif isinstance(sensors, list):
            for d in sensors:
                d = deepcopy(d)
                d["_source_file"] = source_file
                out.append(d)
    elif isinstance(legacy, dict):
        # fallback: treat each key as device
        for k, d in legacy.items():
            if isinstance(d, dict) and ("id" in d or "name" in d):
                d = deepcopy(d)
                d["_source_file"] = source_file
                d["id"] = d.get("id", k)
                out.append(d)
    return out

def build_legacy_index(legacy_dicts):
    # Returns: {normalized_id: [device_dict, ...]}
    index = defaultdict(list)
    for dev, source_file in legacy_dicts:
        for idval in all_possible_ids(dev):
            index[idval].append(dev)
    return index

def extract_field(dev, field):
    # Handles nested fields like location.room
    if "." in field:
        parts = field.split(".")
        val = dev
        for p in parts:
            if isinstance(val, dict):
                val = val.get(p)
            else:
                return None
        return val
    return dev.get(field)

def is_empty(val):
    return val in (None, [], {}, "")

def merge_array_values(values):
    # Deduplicate, flatten, handle dicts by hashing with json.dumps
    out = []
    seen = set()
    for v in values:
        if isinstance(v, list):
            for i in v:
                if isinstance(i, dict):
                    key = json.dumps(i, sort_keys=True)
                else:
                    key = i
                if key not in seen:
                    out.append(i)
                    seen.add(key)
        else:
            if isinstance(v, dict):
                key = json.dumps(v, sort_keys=True)
            else:
                key = v
            if key not in seen:
                out.append(v)
                seen.add(key)
    return out

def resolve_conflict(candidates):
    # Prefer most recent (if timestamps), else most populated, else first
    # Here, just pick the most populated (longest list), else first
    if not candidates:
        return None
    if all(isinstance(c[0], list) for c in candidates):
        return max(candidates, key=lambda x: len(x[0]))
    return candidates[0]

# --- MAIN ---
def main():
    omega = load_json(OMEGA_PATH)
    if not omega:
        print(f"ERROR: Could not load Omega registry from {OMEGA_PATH}. Aborting.")
        return
    legacy_objs = {k: load_json(p) for k, p in LEGACY_PATHS.items()}
    # Flatten all legacy devices
    legacy_devices = []
    for k, obj in legacy_objs.items():
        legacy_devices.extend([(d, k) for d in flatten_legacy_devices(obj, k)])
    # Build index
    legacy_index = build_legacy_index(legacy_devices)
    report = []
    provenance = defaultdict(lambda: defaultdict(list))
    conflicts = defaultdict(lambda: defaultdict(list))
    unresolved = defaultdict(list)
    total_devices = 0
    populated_fields = defaultdict(int)

    for device in omega.get("devices", []):
        total_devices += 1
        device_ids = all_possible_ids(device)
        legacy_matches = []
        for idval in device_ids:
            legacy_matches.extend(legacy_index.get(normalize_key(idval), []))
        # Deduplicate matches
        seen = set()
        unique_matches = []
        for d in legacy_matches:
            did = d.get("id")
            if did and did not in seen:
                unique_matches.append(d)
                seen.add(did)
        # --- Entity subfield handling ---
        if "entities" in device and isinstance(device["entities"], list):
            for i, entity in enumerate(device["entities"]):
                for subfield in [
                    "entities.state", "entities.device_class", "entities.unit_of_measurement", "entities.name", "entities.domain"
                ]:
                    field_name = subfield.split(".")[1]
                    if is_empty(entity.get(field_name)):
                        candidates = []
                        for match in unique_matches:
                            if "entities" in match and isinstance(match["entities"], list):
                                for legacy_entity in match["entities"]:
                                    for legacy_field in FIELD_SYNONYMS[subfield]:
                                        value = extract_field(legacy_entity, legacy_field)
                                        if not is_empty(value):
                                            candidates.append((value, match.get("_source_file", "unknown"), legacy_field))
                        if not candidates:
                            unresolved[subfield].append(f"{device.get('id')}[{i}]")
                        elif len(set([str(c[0]) for c in candidates])) == 1:
                            entity[field_name] = candidates[0][0]
                            provenance[device.get("id")][subfield].append({"entity_index": i, "source": candidates[0][1], "legacy_field": candidates[0][2], "value": candidates[0][0]})
                            populated_fields[subfield] += 1
                        else:
                            chosen = resolve_conflict(candidates)
                            if chosen is not None:
                                entity[field_name] = chosen[0]
                                conflicts[device.get("id")][subfield] = [{"entity_index": i, "source": c[1], "legacy_field": c[2], "value": c[0]} for c in candidates]
                                provenance[device.get("id")][subfield].append({"entity_index": i, "source": chosen[1], "legacy_field": chosen[2], "value": chosen[0]})
                                populated_fields[subfield] += 1
                            else:
                                unresolved[subfield].append(f"{device.get('id')}[{i}]")
        # --- End entity subfield handling ---
        for field, legacy_fields in FIELD_SYNONYMS.items():
            if field.startswith("entities."):
                continue  # Already handled above
            # --- Nested field assignment ---
            if "." in field:
                parent, child = field.split(".", 1)
                if parent not in device or not isinstance(device[parent], dict):
                    device[parent] = {}
                if is_empty(device[parent].get(child)):
                    candidates = []
                    for match in unique_matches:
                        for legacy_field in legacy_fields:
                            value = extract_field(match, legacy_field)
                            if not is_empty(value):
                                candidates.append((value, match.get("_source_file", "unknown"), legacy_field))
                    if not candidates:
                        unresolved[field].append(device.get("id") or device.get("name"))
                    elif len(set([str(c[0]) for c in candidates])) == 1:
                        device[parent][child] = candidates[0][0]
                        provenance[device.get("id")][field].append({"source": candidates[0][1], "legacy_field": candidates[0][2], "value": candidates[0][0]})
                        populated_fields[field] += 1
                    else:
                        chosen = resolve_conflict(candidates)
                        if chosen is not None:
                            device[parent][child] = chosen[0]
                            conflicts[device.get("id")][field] = [{"source": c[1], "legacy_field": c[2], "value": c[0]} for c in candidates]
                            provenance[device.get("id")][field].append({"source": chosen[1], "legacy_field": chosen[2], "value": chosen[0]})
                            populated_fields[field] += 1
                        else:
                            unresolved[field].append(device.get("id") or device.get("name"))
                continue
            # --- End nested field assignment ---
            if is_empty(device.get(field)):
                candidates = []
                for match in unique_matches:
                    for legacy_field in legacy_fields:
                        value = extract_field(match, legacy_field)
                        if not is_empty(value):
                            candidates.append((value, match.get("_source_file", "unknown"), legacy_field))
                # --- Array merge logic ---
                if field in ["aliases", "device_groups", "capabilities"]:
                    merged = merge_array_values([c[0] for c in candidates])
                    if merged:
                        device[field] = merged
                        for v in merged:
                            provs = [c for c in candidates if c[0] == v]
                            for prov in provs:
                                provenance[device.get("id")][field].append({"source": prov[1], "legacy_field": prov[2], "value": v})
                        populated_fields[field] += 1
                    else:
                        unresolved[field].append(device.get("id") or device.get("name"))
                    continue
                # --- End array merge logic ---
                if not candidates:
                    unresolved[field].append(device.get("id") or device.get("name"))
                elif len(set([str(c[0]) for c in candidates])) == 1:
                    device[field] = candidates[0][0]
                    provenance[device.get("id")][field].append({"source": candidates[0][1], "legacy_field": candidates[0][2], "value": candidates[0][0]})
                    populated_fields[field] += 1
                else:
                    chosen = resolve_conflict(candidates)
                    if chosen is not None:
                        device[field] = chosen[0]
                        conflicts[device.get("id")][field] = [{"source": c[1], "legacy_field": c[2], "value": c[0]} for c in candidates]
                        provenance[device.get("id")][field].append({"source": chosen[1], "legacy_field": chosen[2], "value": chosen[0]})
                        populated_fields[field] += 1
                    else:
                        unresolved[field].append(device.get("id") or device.get("name"))
    # Save enriched registry
    with open(OMEGA_PATH, "w", encoding="utf-8") as f:
        json.dump(omega, f, ensure_ascii=False, indent=2)
    # Write report
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(f"Omega Registry Enrichment Report - {datetime.now()}\n\n")
        f.write(f"Total devices processed: {total_devices}\n\n")
        f.write("Populated fields (with provenance):\n")
        for dev_id, fields in provenance.items():
            f.write(f"Device {dev_id}:\n")
            for field, provs in fields.items():
                for prov in provs:
                    f.write(f"  {field}: {prov}\n")
        f.write("\nConflicts:\n")
        for dev_id, fields in conflicts.items():
            f.write(f"Device {dev_id}:\n")
            for field, vals in fields.items():
                f.write(f"  {field}: {vals}\n")
        f.write("\nUnresolved/null fields after enrichment:\n")
        for field, ids in unresolved.items():
            f.write(f"Field '{field}' still null/empty for {len(ids)} devices: {ids}\n")
        f.write("\nCoverage metrics (populated fields):\n")
        for field, count in populated_fields.items():
            f.write(f"{field}: {count} populated\n")
    print(f"Enrichment complete. Report written to {REPORT_PATH}")

if __name__ == "__main__":
    main()

# PATCH: All master.omega_registry/ path references removed; now using project-root-relative or config-driven paths only.
