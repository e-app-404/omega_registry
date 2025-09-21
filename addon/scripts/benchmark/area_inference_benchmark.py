import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import json
import re
import yaml
from pathlib import Path
from datetime import datetime
from registry.utils.registry import load_json
from registry.utils.constants import COMMON_AREAS
from registry.utils.inference import infer_area_id
from registry.utils.cluster import build_device_map

def main():
    # Load config
    settings_path = Path(__file__).parent.parent.parent / "settings.conf.yaml"
    with open(settings_path) as f:
        settings_yaml = yaml.safe_load(f)
    if "settings" in settings_yaml:
        settings = settings_yaml["settings"]
    else:
        settings = settings_yaml
    if "general" in settings:
        input_paths = settings["general"]["input_paths"]
    else:
        raise KeyError("Could not find 'general' key in settings.conf.yaml; please check your config structure.")
    entity_registry = load_json(input_paths["core_entity_registry"])
    try:
        device_registry = load_json(input_paths["core_device_registry"])
        device_map = build_device_map(device_registry)
    except Exception:
        device_map = {}
    entities = entity_registry.get('data', {}).get('entities', entity_registry.get('entities', []))
    methods = [
        ("centralized_infer_area_id", lambda e, d: infer_area_id(e, d, set(COMMON_AREAS))),
    ]
    results = {}
    for name, fn in methods:
        success = 0
        breakdown = {}
        for e in entities:
            area = fn(e, device_map)
            if area:
                success += 1
                breakdown[area] = breakdown.get(area, 0) + 1
        results[name] = {
            "total": len(entities),
            "success": success,
            "success_rate": round(success / len(entities) * 100, 2) if entities else 0,
            "unique_areas": len(breakdown),
            "area_breakdown": breakdown,
        }
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = Path(__file__).parent.parent.parent / f"data/area_inference_benchmark_{ts}.log"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Area inference benchmark complete. Results written to {out_path}")

if __name__ == "__main__":
    main()
