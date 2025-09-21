import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))
import json
from pathlib import Path
from registry.utils.registry import load_entity_registry, load_device_registry

# --- Load Inputs ---
ENTITY_REG_PATH = Path("input/core.entity_registry")
DEVICE_REG_PATH = Path("input/core.device_registry")
AREA_REG_PATH = Path("input/core.area_registry")
OUTPUT_DIR = Path("output/audit_phase_roundtrip/")
LOG_PATH = OUTPUT_DIR / "PATCH-ROUNDTRIP-AUDIT-V2.log"

OUTPUTS = {
    "orphaned": OUTPUT_DIR / "orphaned_entity_ids.json",
    "devices_wo_area": OUTPUT_DIR / "devices_without_area.json",
    "missing_fields": OUTPUT_DIR / "entities_with_missing_fields.json",
    "unlinked": OUTPUT_DIR / "unlinked_entities_trace.json",
    "summary": OUTPUT_DIR / "phase1_audit_summary.json",
}

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_area_registry(path):
    with open(path, "r") as f:
        data = json.load(f)
    return {a["id"]: a for a in data["data"]["areas"]}

entity_registry = load_entity_registry(ENTITY_REG_PATH)["entities"]
device_registry = load_device_registry(DEVICE_REG_PATH)["devices"]
area_registry = load_area_registry(AREA_REG_PATH)

device_map = {d["id"]: d for d in device_registry}
area_ids = set(area_registry.keys())

# --- Audit Results ---
orphaned_entities = []
devices_without_area = []
entities_missing_fields = []
unlinked_entities = []
fully_linked_entities = 0

for ent in entity_registry:
    eid = ent.get("entity_id")
    did = ent.get("device_id")
    name = ent.get("name")
    # --- PATCH-INSTRUCTION: DOMAIN & DEVICE_CLASS VALIDATION LOGIC ---
    entity_id = ent.get("entity_id", "")
    domain = ent.get("domain") or (entity_id.split(".", 1)[0] if "." in entity_id else None)
    if "domain" not in ent and domain:
        ent["domain"] = domain
    platform = ent.get("platform")
    device_class = ent.get("device_class")
    missing_fields = []
    if not domain:
        missing_fields.append("domain")
    if not platform:
        missing_fields.append("platform")
    DEVICE_CLASS_REQUIRED_DOMAINS = {"sensor", "binary_sensor"}
    if domain in DEVICE_CLASS_REQUIRED_DOMAINS and not device_class:
        missing_fields.append("device_class")
    if missing_fields:
        entities_missing_fields.append({
            "entity_id": eid,
            "device_id": did,
            "name": name,
            "domain": domain,
            "platform": platform,
            "device_class": device_class,
            "missing_fields": missing_fields,
            "reason": f"Missing required field(s): {', '.join(missing_fields)}"
        })
    # a. Orphaned Entities
    if not did or did not in device_map:
        orphaned_entities.append({
            "entity_id": eid,
            "device_id": did,
            "name": name,
            "platform": platform,
            "domain": domain,
            "device_class": device_class,
            "reason": "device_id not found in device registry"
        })
    # d. Unlinked Entities
    linkage_status = "fully_linked"
    reason = None
    if not did or did not in device_map:
        linkage_status = "orphaned_entity"
        reason = "device_id missing or not found"
    else:
        device = device_map[did]
        area_id = ent.get("area_id") or device.get("area_id")
        if not area_id or area_id not in area_ids:
            linkage_status = "unlinked_entity"
            reason = "area_id missing or not found in area registry"
    if linkage_status != "fully_linked":
        unlinked_entities.append({
            "entity_id": eid,
            "device_id": did,
            "name": name,
            "platform": platform,
            "domain": domain,
            "device_class": device_class,
            "linkage_status": linkage_status,
            "reason": reason
        })
    else:
        fully_linked_entities += 1

for dev in device_registry:
    did = dev.get("id")
    name = dev.get("name")
    area_id = dev.get("area_id")
    if not area_id or area_id not in area_ids:
        devices_without_area.append({
            "device_id": did,
            "name": name,
            "area_id": area_id,
            "reason": "area_id missing or not found in area registry"
        })

# --- Write Outputs ---
with open(OUTPUTS["orphaned"], "w") as f:
    json.dump(orphaned_entities, f, indent=2)
with open(OUTPUTS["devices_wo_area"], "w") as f:
    json.dump(devices_without_area, f, indent=2)
with open(OUTPUTS["missing_fields"], "w") as f:
    json.dump(entities_missing_fields, f, indent=2)
with open(OUTPUTS["unlinked"], "w") as f:
    json.dump(unlinked_entities, f, indent=2)

summary = {
    "total_entities_inspected": len(entity_registry),
    "total_devices_inspected": len(device_registry),
    "orphaned_entities": len(orphaned_entities),
    "devices_without_area": len(devices_without_area),
    "entities_missing_required_fields": len(entities_missing_fields),
    "fully_linked_entities": fully_linked_entities
}
with open(OUTPUTS["summary"], "w") as f:
    json.dump(summary, f, indent=2)

# --- Log ---
with open(LOG_PATH, "a") as log:
    log.write(f"[Phase 1] Entity count: {len(entity_registry)}\n")
    log.write(f"[Phase 1] Device count: {len(device_registry)}\n")
    log.write(f"[Phase 1] Orphaned entities: {len(orphaned_entities)} -> {OUTPUTS['orphaned'].name}\n")
    log.write(f"[Phase 1] Devices without area: {len(devices_without_area)} -> {OUTPUTS['devices_wo_area'].name}\n")
    log.write(f"[Phase 1] Entities missing required fields: {len(entities_missing_fields)} -> {OUTPUTS['missing_fields'].name}\n")
    log.write(f"[Phase 1] Unlinked entities: {len(unlinked_entities)} -> {OUTPUTS['unlinked'].name}\n")
    log.write(f"[Phase 1] Fully linked entities: {fully_linked_entities}\n")
    log.write(f"[Phase 1] Summary: {OUTPUTS['summary'].name}\n")
    if not orphaned_entities:
        log.write("[Phase 1] No orphaned entities found.\n")
    if not devices_without_area:
        log.write("[Phase 1] All devices have valid area_id.\n")
    if not entities_missing_fields:
        log.write("[Phase 1] All entities have required fields.\n")
    if not unlinked_entities:
        log.write("[Phase 1] All entities are fully linked.\n")
    log.write("---\n")
print("[Phase 1] Audit complete. Outputs written to output/audit_phase_roundtrip/")
