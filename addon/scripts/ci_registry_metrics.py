import json
from collections import Counter
from datetime import datetime
import sys
import os
from registry.utils.constants import COMMON_AREAS
from registry.utils.registry import load_yaml

# Load config
settings = load_yaml("settings.conf.yaml")["settings"]
output_paths = settings["output_paths"]
# --- [AUDIT deprecated path usage] Patch: replaced hardcoded paths with config-driven paths ---
with open(os.path.join(os.path.dirname(__file__), '../conversation_full_history.log'), "a") as log:
    log.write("[PATCH-CONFIG-CONSISTENCY-V1] [AUDIT deprecated path usage] ci_registry_metrics.py: replaced hardcoded paths with settings['output_paths'] from settings.conf.yaml\n")

REGISTRY_PATH = output_paths.get("omega_enriched_devtools", "output/omega_device_registry.enriched.canonical.devtools_enriched.json")
# Use FIELD_SYNONYMS keys as SCHEMA_KEYS for consistency
SCHEMA_KEYS = [
    "preferred_protocol", "fallback_settings", "via_device_id", "integration", "area_id", "room", "zone"
]

def is_empty(val):
    return val is None or val == "" or val == [] or val == {}

def main():
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        data = json.load(f)
    devices = data.get("devices", [])
    lines = []
    lines.append(f"Total devices: {len(devices)}\n")

    # Metrics: Populated vs Null/Empty
    lines.append("Field Population Metrics:")
    for key in SCHEMA_KEYS:
        populated = 0
        empty = 0
        for d in devices:
            if key in d and not is_empty(d[key]):
                populated += 1
            else:
                empty += 1
        lines.append(f"  {key:20}  populated: {populated:4}   empty/null: {empty:4}")

    lines.append("\nValue Distributions (top 10 per key):")
    for key in SCHEMA_KEYS:
        counter = Counter()
        for d in devices:
            val = d.get(key)
            if isinstance(val, (list, dict)):
                val = str(val)
            counter[val] += 1
        lines.append(f"\nKey: {key}")
        for value, count in counter.most_common(10):
            lines.append(f"  {repr(value):30} : {count}")

    # Print to stdout
    for line in lines:
        print(line)

    # Save to file with timestamp
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    out_path = f"output/data/ci_registry_metrics_{ts}.log"
    with open(out_path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")
    print(f"\nMetrics saved to {out_path}")

if __name__ == "__main__":
    main()
