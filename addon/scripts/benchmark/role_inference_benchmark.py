import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Load registry data
ROOT = Path(__file__).parent.parent.parent
ENTITY_REGISTRY_PATH = ROOT / "input" / "core.entity_registry.json"
DEVICE_REGISTRY_PATH = ROOT / "input" / "core.device_registry.json"

# Output
DATA_DIR = ROOT / "output" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = DATA_DIR / f"role_inference_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# --- Role inference strategies ---
def infer_cluster_role(entity):
    for key in ['device_class', 'original_device_class']:
        if entity.get(key):
            return entity[key]
    if entity.get('original_name'):
        return entity['original_name']
    eid = entity.get('entity_id', '')
    for role in ['motion', 'occupancy', 'temperature', 'humidity', 'button', 'switch', 'light', 'media_player']:
        if role in eid:
            return role
    return None

def infer_device_class(entity, standard_device_classes):
    device_class = entity.get("device_class")
    if device_class and device_class in standard_device_classes:
        return device_class
    eid = entity.get("entity_id")
    if eid and "." in eid:
        domain = eid.split(".")[0]
        if domain in standard_device_classes:
            return domain
    return None

def get_role(entity, entity_features):
    eid = entity.get("entity_id")
    # Try domain as role
    if eid and "." in eid:
        domain = eid.split(".")[0]
        if domain in ["sensor", "switch", "light", "binary_sensor", "cover", "climate", "media_player", "lock", "button", "input_boolean"]:
            return domain
    # Try friendly_name or name as fallback
    name = entity.get("friendly_name") or entity.get("name")
    if name:
        name = name.lower()
        for role in entity_features:
            if role in name:
                return role
    # Try slug as fallback
    slug = eid.split(".")[1] if eid and "." in eid else None
    if slug:
        for role in entity_features:
            if role in slug:
                return role
    return None

# --- Load constants ---
CONSTANTS_PATH = ROOT / "registry" / "utils" / "constants.py"
STANDARD_DEVICE_CLASSES = set()
ENTITY_FEATURES = set()
if CONSTANTS_PATH.exists():
    with open(CONSTANTS_PATH) as f:
        content = f.read()
        import ast
        tree = ast.parse(content)
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if target.id == "STANDARD_DEVICE_CLASSES":
                            STANDARD_DEVICE_CLASSES = set(ast.literal_eval(node.value))
                        if target.id == "ENTITY_FEATURES":
                            ENTITY_FEATURES = set(ast.literal_eval(node.value))

# --- Load registry data ---
with open(ROOT / "input" / "core.entity_registry") as f:
    entity_registry = json.load(f)
entities = entity_registry.get('data', {}).get('entities', entity_registry.get('entities', []))

# --- Benchmark ---
results = []
cluster_role_success = 0
device_class_role_success = 0
get_role_success = 0
for entity in entities:
    eid = entity.get("entity_id")
    r1 = infer_cluster_role(entity)
    r2 = infer_device_class(entity, STANDARD_DEVICE_CLASSES)
    r3 = get_role(entity, ENTITY_FEATURES)
    if r1:
        cluster_role_success += 1
    if r2:
        device_class_role_success += 1
    if r3:
        get_role_success += 1
    results.append({
        "entity_id": eid,
        "cluster_role": r1,
        "device_class_role": r2,
        "get_role": r3
    })

# --- Analysis ---
agree = 0
disagree = 0
missing = 0
for r in results:
    roles = [r["cluster_role"], r["device_class_role"], r["get_role"]]
    roles_set = set([x for x in roles if x])
    if not roles_set:
        missing += 1
    elif len(roles_set) == 1:
        agree += 1
    else:
        disagree += 1

total = len(results)
with open(LOG_PATH, "w") as f:
    f.write(f"Total entities: {total}\n")
    f.write(f"All agree: {agree}\n")
    f.write(f"Disagree: {disagree}\n")
    f.write(f"Missing (no role inferred): {missing}\n\n")
    f.write(f"cluster_role success rate: {cluster_role_success}/{total} ({round(cluster_role_success/total*100,2)}%)\n")
    f.write("cluster_role logic: (see autocluster_audit.py)\n")
    f.write('''
def infer_cluster_role(entity):
    for key in ['device_class', 'original_device_class']:
        if entity.get(key):
            return entity[key]
    if entity.get('original_name'):
        return entity['original_name']
    eid = entity.get('entity_id', '')
    for role in ['motion', 'occupancy', 'temperature', 'humidity', 'button', 'switch', 'light', 'media_player']:
        if role in eid:
            return role
    return None
''')
    f.write(f"device_class_role success rate: {device_class_role_success}/{total} ({round(device_class_role_success/total*100,2)}%)\n")
    f.write("device_class_role logic: (see fingerprint_entity_reconciliation.py)\n")
    f.write('''
def infer_device_class(entity):
    device_class = entity.get('device_class')
    if device_class and device_class in STANDARD_DEVICE_CLASSES:
        return device_class
    eid = entity.get('entity_id')
    if eid and '.' in eid:
        domain = eid.split('.')[0]
        if domain in STANDARD_DEVICE_CLASSES:
            return domain
    return None
''')
    f.write(f"get_role success rate: {get_role_success}/{total} ({round(get_role_success/total*100,2)}%)\n")
    f.write("get_role logic: (see fingerprint_entity_reconciliation.py)\n")
    f.write('''
def get_role(entity, entity_features):
    eid = entity.get('entity_id')
    if eid and '.' in eid:
        domain = eid.split('.')[0]
        if domain in ["sensor", "switch", "light", "binary_sensor", "cover", "climate", "media_player", "lock", "button", "input_boolean"]:
            return domain
    name = entity.get('friendly_name') or entity.get('name')
    if name:
        name = name.lower()
        for role in entity_features:
            if role in name:
                return role
    slug = eid.split('.')[1] if eid and '.' in eid else None
    if slug:
        for role in entity_features:
            if role in slug:
                return role
    return None
''')
    f.write("\nSample disagreements:\n")
    for r in results:
        roles = [r["cluster_role"], r["device_class_role"], r["get_role"]]
        roles_set = set([x for x in roles if x])
        if len(roles_set) > 1:
            f.write(json.dumps(r) + "\n")

print(f"Role inference benchmark complete. Log written to {LOG_PATH}")
