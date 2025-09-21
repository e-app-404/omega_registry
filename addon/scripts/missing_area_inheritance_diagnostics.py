import json
from collections import defaultdict

# Load entity fingerprint map
with open('output/entity_fingerprint_map.json') as f:
    entity_map = json.load(f)

# Load device registry
with open('output/omega_device_registry.enriched.canonical.json') as f:
    device_registry = json.load(f)["devices"]

device_area_map = {d["id"]: d.get("area_id") for d in device_registry}

diagnostics = []
for entity_id, entity in entity_map.items():
    final_area = entity.get("final_area")
    area_inference_source = entity.get("area_inference_source")
    device_id = entity.get("device_id")
    inherited = False
    device_area_id = None
    reason = None
    if (final_area in (None, "unknown_area") and (not area_inference_source or area_inference_source != "device")):
        if device_id and device_id in device_area_map:
            device_area_id = device_area_map[device_id]
            if device_area_id:
                inherited = False
                reason = "device area exists but was not propagated"
            else:
                reason = "device has no area_id"
        else:
            reason = "no device_id or device not found"
        diagnostics.append({
            "entity_id": entity_id,
            "device_id": device_id,
            "device_area_id": device_area_id,
            "inherited": inherited,
            "reason": reason
        })

with open('output/omega_room/missing_area_inheritance_diagnostics.json', 'w') as f:
    json.dump(diagnostics, f, indent=2)
