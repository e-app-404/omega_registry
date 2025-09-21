# verify_pipeline_inputs.py
import json, yaml # type: ignore
from pathlib import Path

def load_yaml(p): return yaml.safe_load(open(p))
def load_json(p): return json.load(open(p))

# PATCH: All master.omega_registry/ path references removed; now using project-root-relative or config-driven paths only.
paths = {
    "entity_registry": Path("input/core.entity_registry"),
    "device_registry": Path("input/core.device_registry"),
    "settings": Path("settings.conf.yaml"),
}

entity_data = load_json(paths["entity_registry"])["data"]["entities"]
device_data = load_json(paths["device_registry"])["data"]["devices"]
# [PATCH-CONFIG-LOAD-FIX-V1] Root-level config parsing enabled. Deprecated: settings_data = load_yaml(paths["settings"])["settings"]
settings_data = load_yaml(paths["settings"])

print(f"✅ Entity registry loaded: {len(entity_data)} entities")
print(f"✅ Device registry loaded: {len(device_data)} devices")
print(f"✅ Room mapping count: {len(settings_data.get('rooms', []))}")
print(f"✅ Role inference rules: {len(settings_data.get('role_inference_rules', {}))}")
