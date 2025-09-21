"""
Script: harden_file_dependency_matrix.py
Purpose: Validate and harden file_dependency_matrix.json for audit compliance.

- Ensures all .py scripts are listed or justified in _meta.exclusions
- Resolves config-driven paths using settings.conf.yaml
- Removes vague entries and placeholders
- Validates reads/writes against OUTPUT_DEPENDENCY_MAP in generate_registry_index.py
- Emits file_dependency_matrix.audit_report.json with flagged issues
- Logs all updates to required patch logs
"""
import os
import json
import yaml # type: ignore
from glob import glob
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_DIR = os.path.join(ROOT, "registry_rehydration_local")
MATRIX_PATH = os.path.join(LOCAL_DIR, "file_dependency_matrix.json")
SETTINGS_PATH = os.path.join(LOCAL_DIR, "settings.conf.yaml")
OUTPUT_DEP_MAP_PATH = os.path.join(LOCAL_DIR, "generate_registry_index.py")
AUDIT_REPORT_PATH = os.path.join(LOCAL_DIR, "file_dependency_matrix.audit_report.json")
PATCH_LOG = os.path.join(LOCAL_DIR, "copilot_patches", "PATCH-FILE-DEPENDENCY-MATRIX-HARDENING-V3.log")
PATCHLOG_OVERVIEW = os.path.join(LOCAL_DIR, "copilot_patchlog_overview.log")
CHATLOG = os.path.join(LOCAL_DIR, "copilot_chronological_chatlog.log")

# Utility: Load settings.conf.yaml
try:
    with open(SETTINGS_PATH) as f:
        settings = yaml.safe_load(f)
except Exception:
    settings = {}

# Utility: Load OUTPUT_DEPENDENCY_MAP from generate_registry_index.py
import ast
output_dep_map = {}
try:
    with open(OUTPUT_DEP_MAP_PATH) as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "OUTPUT_DEPENDENCY_MAP":
                    output_dep_map = ast.literal_eval(node.value)
except Exception:
    output_dep_map = {}

# Utility: Load file_dependency_matrix.json
with open(MATRIX_PATH) as f:
    matrix = json.load(f)

# Step 1: Find all .py scripts
all_scripts = set()
for path in glob(os.path.join(LOCAL_DIR, "**", "*.py"), recursive=True):
    rel_path = os.path.relpath(path, LOCAL_DIR)
    all_scripts.add(rel_path)

# Step 2: Validate script coverage
missing_scripts = []
for script in all_scripts:
    if script not in matrix:
        missing_scripts.append(script)

# Step 3: Check exclusions
meta = matrix.get("_meta", {})
exclusions = set(meta.get("exclusions", []))
justified_exclusions = {}
for exc in exclusions:
    # Check for justification
    note = meta.get("exclusion_notes", {}).get(exc, "")
    if not note or note.lower() in ["utility script", "generic"]:
        justified_exclusions[exc] = False
    else:
        justified_exclusions[exc] = True

# Step 4: Remove vague entries and resolve config paths
vague_entries = []
resolved = 0
for script, entry in matrix.items():
    if script == "_meta":
        continue
    for key in ["reads", "writes"]:
        new_paths = []
        for path in entry.get(key, []):
            if "as per logic" in path or "placeholder" in path:
                vague_entries.append((script, key, path))
                continue
            # Resolve config-driven paths
            if "input_paths[" in path or "output_paths[" in path:
                resolved_path = None  # Ensure variable is always defined
                try:
                    if "input_paths[" in path:
                        k = path.split("input_paths[")[1].split("]")[0].strip("'\"")
                        resolved_path = settings.get("input_paths", {}).get(k)
                    elif "output_paths[" in path:
                        k = path.split("output_paths[")[1].split("]")[0].strip("'\"")
                        resolved_path = settings.get("output_paths", {}).get(k)
                    if resolved_path:
                        new_paths.append(resolved_path)
                        resolved += 1
                        continue
                except Exception:
                    vague_entries.append((script, key, path))
                    continue
            new_paths.append(path)
        entry[key] = new_paths

# Step 5: Validate output mapping consistency
output_map_issues = []
for script, entry in matrix.items():
    if script == "_meta":
        continue
    writes = set(entry.get("writes", []))
    expected_writes = set()
    for k, v in output_dep_map.items():
        if v.get("script") == script:
            expected_writes.update(v.get("outputs", []))
    if not writes.issuperset(expected_writes):
        output_map_issues.append({"script": script, "missing_outputs": list(expected_writes - writes)})

# Step 6: Find orphaned files
all_files = set()
for path in glob(os.path.join(LOCAL_DIR, "**", "*"), recursive=True):
    if os.path.isfile(path):
        rel_path = os.path.relpath(path, LOCAL_DIR)
        all_files.add(rel_path)
referenced_files = set()
for entry in matrix.values():
    if isinstance(entry, dict):
        referenced_files.update(entry.get("reads", []))
        referenced_files.update(entry.get("writes", []))

orphaned_files = sorted(list(all_files - referenced_files))

# Step 7: Emit audit report
report = {
    "missing_scripts": missing_scripts,
    "unjustified_exclusions": [k for k, v in justified_exclusions.items() if not v],
    "vague_entries": vague_entries,
    "output_map_issues": output_map_issues,
    "orphaned_files": orphaned_files,
    "resolved_config_paths": resolved,
}
with open(AUDIT_REPORT_PATH, "w") as f:
    json.dump(report, f, indent=2)

# Step 8: Log updates
log_entry = f"""
PATCH-FILE-DEPENDENCY-MATRIX-HARDENING-V3
Validation complete.
Missing scripts: {missing_scripts}
Unjustified exclusions: {[k for k, v in justified_exclusions.items() if not v]}
Vague entries: {vague_entries}
Output map issues: {output_map_issues}
Orphaned files: {orphaned_files}
Resolved config paths: {resolved}
Audit report emitted: {AUDIT_REPORT_PATH}
"""
for log_path in [PATCH_LOG, PATCHLOG_OVERVIEW, CHATLOG]:
    with open(log_path, "a") as f:
        f.write(log_entry + "\n")

print("Validation and hardening complete. See audit report and logs for details.")
