import json
import os
import yaml # type: ignore

# Load config
settings_path = os.path.join(os.path.dirname(__file__), '../settings.conf.yaml')
with open(settings_path) as f:
    settings_yaml = yaml.safe_load(f)
settings = settings_yaml["settings"]
output_paths = settings["output_paths"]
# --- [AUDIT deprecated path usage] Patch: replaced hardcoded paths with config-driven paths ---
with open(os.path.join(os.path.dirname(__file__), '../conversation_full_history.log'), "a") as log:
    log.write("[PATCH-CONFIG-CONSISTENCY-V1] [AUDIT deprecated path usage] condense_identifiers.py: replaced hardcoded paths with settings['output_paths'] from settings.conf.yaml\n")

INPUT_PATH = output_paths.get("omega_enriched_stage2", os.path.join(os.path.dirname(__file__), "omega_device_registry.enriched.canonical.json"))
OUTPUT_PATH = INPUT_PATH + ".tmp"

with open(INPUT_PATH, "r") as f:
    data = json.load(f)

def custom_dump(obj, fp):
    # Custom JSON dump to force identifiers to be in-line
    def default(o):
        return o
    def iterencode(obj, _indent_level=0):
        if isinstance(obj, dict):
            yield '{\n'
            first = True
            for k, v in obj.items():
                if not first:
                    yield ',\n'
                first = False
                yield '  ' * (_indent_level + 1) + json.dumps(k) + ': '
                if k == "identifiers" and isinstance(v, list):
                    # Inline array of arrays
                    yield json.dumps(v, separators=(',', ': '))
                else:
                    for chunk in iterencode(v, _indent_level + 1):
                        yield chunk
            yield '\n' + '  ' * _indent_level + '}'
        elif isinstance(obj, list):
            yield '[\n'
            for i, v in enumerate(obj):
                if i > 0:
                    yield ',\n'
                yield '  ' * (_indent_level + 1)
                for chunk in iterencode(v, _indent_level + 1):
                    yield chunk
            yield '\n' + '  ' * _indent_level + ']'
        else:
            yield json.dumps(obj)
    for chunk in iterencode(obj):
        fp.write(chunk)

with open(OUTPUT_PATH, "w") as f:
    custom_dump(data, f)

print(f"Identifiers fields are now in-line. Output: {OUTPUT_PATH}")

# PATCH: All master.omega_registry/ path references removed; now using project-root-relative or config-driven paths only.
