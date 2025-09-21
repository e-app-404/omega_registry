import json
import os

ENTITY_REGISTRY_PATH = "input/post-reboot.ha_registries/core.entity_registry"
DEVICE_REGISTRY_PATH = "input/post-reboot.ha_registries/core.device_registry"
OUTPUT_PATH = "canonical/omega_registry/omega_registry_master.json"

# Load entity registry
def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def main():
    if not os.path.exists(ENTITY_REGISTRY_PATH) or not os.path.exists(DEVICE_REGISTRY_PATH):
        print(f"ERROR: Input registry files not found.")
        return
    with open(ENTITY_REGISTRY_PATH, "r", encoding="utf-8") as f:
        entity_registry = json.load(f)
    with open(DEVICE_REGISTRY_PATH, "r", encoding="utf-8") as f:
        device_registry = json.load(f)
    devices = {d["id"]: d for d in device_registry.get("data", {}).get("devices", [])}
    entities = entity_registry.get("data", {}).get("entities", [])
    output_entities = []
    for entity in entities:
        enriched = dict(entity)  # Only verifiable fields from entity
        device_id = entity.get("device_id")
        if device_id and device_id in devices:
            device = devices[device_id]
            # Merge only verifiable, non-inferred device fields
            for k, v in device.items():
                if k not in enriched:
                    enriched[k] = v
        output_entities.append(enriched)
    output = {
        "version": 1,
        "source": "canonical_registry_builder_v1",
        "entities": output_entities
    }
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Canonical omega registry written: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
