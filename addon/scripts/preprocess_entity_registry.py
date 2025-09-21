import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent / "registry"))
from registry.utils.registry import load_json, load_yaml
from registry.utils.pathing import resolve_path
from registry.utils.synonyms import normalize_attribute
from registry.utils.constants import PRESERVE_AUXILIARY_FIELDS

def normalize_entity(entity):
    # Required fields
    normalized = {
        "entity_id": entity.get("entity_id"),
        "platform": entity.get("platform"),
        "device_id": entity.get("device_id"),
        "original_name": entity.get("original_name") or entity.get("name"),
        "device_class": entity.get("device_class"),
        "area_id": entity.get("area_id"),
        "domain": entity.get("domain"),
        "integration": entity.get("integration"),
    }
    # Optional enrichment
    eid = entity.get("entity_id", "")
    normalized["slug"] = eid.split(".")[-1] if "." in eid else eid
    if not normalized["domain"] and "." in eid:
        normalized["domain"] = eid.split(".")[0]
    if not normalized["platform"]:
        normalized["platform"] = normalized["domain"]
    normalized["normalized_platform"] = normalize_attribute(normalized["platform"])
    # Enrich with auxiliary fields
    for key in PRESERVE_AUXILIARY_FIELDS:
        if key in entity:
            normalized[key] = entity[key]
    return normalized

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="settings.conf.yaml")
    args = parser.parse_args()
    settings_path = os.path.join(os.path.dirname(__file__), '../' + args.config)
    settings = load_yaml(settings_path)
    input_paths = settings["paths"]
    entity_registry_path = str(resolve_path(input_paths.get("core_entity_registry", "input/core.entity_registry")))
    device_registry_path = str(resolve_path(input_paths.get("core_device_registry", "input/core.device_registry")))
    entity_registry = load_json(entity_registry_path)
    # Optionally load device registry for enrichment (not used here, but available)
    # device_registry = load_json(device_registry_path)
    entities = entity_registry["data"]["entities"]
    normalized_entities = [normalize_entity(e) for e in entities]
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    out_dir = Path("data")
    out_dir.mkdir(exist_ok=True)
    normalized_path = out_dir / f"entities.normalized.{ts}.json"
    log_path = out_dir / f"entity_preprocessing_log.{ts}.json"
    with open(normalized_path, "w") as f:
        json.dump(normalized_entities, f, indent=2)
    log = {
        "timestamp": ts,
        "input_entity_count": len(entities),
        "output_entity_count": len(normalized_entities),
        "status": "✅ complete",
        "notes": "All entities preserved; structural normalization only. No semantic filtering applied."
    }
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)
    print(f"Normalized entity registry written to {normalized_path}")
    print(f"Log written to {log_path}")

if __name__ == "__main__":
    main()
