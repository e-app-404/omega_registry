import json
from pathlib import Path

FINGERPRINT_PATH = Path("output/fingerprinting_run/entity_fingerprint_map.json")
DIAGNOSTICS_PATH = Path("output/fingerprinting_run/area_resolution_diagnostics.json")
OUTPUT_DIR = Path("output/audit_phase_roundtrip/")
LOG_PATH = OUTPUT_DIR / "PATCH-ROUNDTRIP-AUDIT-V2.log"
PATCHLOG_PATH = Path("copilot_patchlog_overview.log")

OUTPUTS = {
    "integrity": OUTPUT_DIR / "fingerprint_integrity_report.json",
    "trace": OUTPUT_DIR / "canonical_key_inference_trace.json",
}

REQUIRED_FIELDS = [
    "role", "semantic_role", "tier", "match_methods", "final_area", "area_inference_source"
]

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load fingerprint map (dict: entity_id -> fingerprint dict)
with open(FINGERPRINT_PATH) as f:
    fingerprint_map = json.load(f)

# Load diagnostics (list of dicts)
with open(DIAGNOSTICS_PATH) as f:
    diagnostics = json.load(f)

diagnostics_by_entity = {d["entity_id"]: d for d in diagnostics if "entity_id" in d}

integrity_report = []
trace_report = []
missing_fields_count = 0
area_mismatch_count = 0
fully_valid_count = 0

def get_canonical_key(entity_id):
    # Use the part before the first dot as canonical key, or fallback to entity_id
    return entity_id.split(".", 1)[-1] if "." in entity_id else entity_id

for entity_id, fp in fingerprint_map.items():
    entry = {
        "entity_id": entity_id,
        "canonical_entity_key": get_canonical_key(entity_id),
        "missing_fields": [],
        "area_match_status": None,
        "reason": None,
        "matched_diagnostics_entry": None
    }
    # 1. Field validation
    for field in REQUIRED_FIELDS:
        if field not in fp or fp[field] in (None, "", []):
            entry["missing_fields"].append(field)
    if entry["missing_fields"]:
        entry["reason"] = f"Missing required field(s): {', '.join(entry['missing_fields'])}"
        missing_fields_count += 1
    # 2. Area propagation cross-validation
    diag = diagnostics_by_entity.get(entity_id)
    if diag:
        entry["matched_diagnostics_entry"] = diag
        area_match = (
            fp.get("final_area") == diag.get("final_area") and
            fp.get("area_inference_source") == diag.get("area_inference_source")
        )
        entry["area_match_status"] = "match" if area_match else "mismatch"
        if not area_match:
            entry["reason"] = (entry["reason"] + "; " if entry["reason"] else "") + "Area propagation mismatch"
            area_mismatch_count += 1
    else:
        entry["area_match_status"] = "no_diagnostics"
        entry["reason"] = (entry["reason"] + "; " if entry["reason"] else "") + "No diagnostics entry found"
    # 3. Trace origin for fallback/variant
    if fp.get("area_inference_source") in ("name_token_fallback", "variant", "fuzzy", "unresolvable"):
        trace_report.append({
            "entity_id": entity_id,
            "canonical_entity_key": get_canonical_key(entity_id),
            "area_inference_source": fp.get("area_inference_source"),
            "final_area": fp.get("final_area"),
            "match_methods": fp.get("match_methods"),
        })
    if not entry["missing_fields"] and entry["area_match_status"] == "match":
        fully_valid_count += 1
    integrity_report.append(entry)

summary = {
    "total_entries_inspected": len(fingerprint_map),
    "entries_missing_fields": missing_fields_count,
    "entries_with_area_propagation_mismatch": area_mismatch_count,
    "fully_valid_entries": fully_valid_count
}

with open(OUTPUTS["integrity"], "w") as f:
    json.dump({"summary": summary, "entries": integrity_report}, f, indent=2)
with open(OUTPUTS["trace"], "w") as f:
    json.dump(trace_report, f, indent=2)

with open(LOG_PATH, "a") as log:
    log.write(f"[Phase 2] Fingerprint entries inspected: {len(fingerprint_map)}\n")
    log.write(f"[Phase 2] Entries missing required fields: {missing_fields_count}\n")
    log.write(f"[Phase 2] Entries with area propagation mismatch: {area_mismatch_count}\n")
    log.write(f"[Phase 2] Fully valid entries: {fully_valid_count}\n")
    log.write(f"[Phase 2] Integrity report: {OUTPUTS['integrity'].name}\n")
    log.write(f"[Phase 2] Canonical key trace: {OUTPUTS['trace'].name}\n")
    log.write("---\n")
with open(PATCHLOG_PATH, "a") as log:
    log.write("[PATCH] Phase 2: Fingerprint Layer Audit completed. See PATCH-ROUNDTRIP-AUDIT-V2.log for details.\n")
print("[Phase 2] Audit complete. Outputs written to output/audit_phase_roundtrip/")
