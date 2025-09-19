#!/usr/bin/env python3
# Run with: python -m scripts.audit.audit_contract_compliance
"""
Audit contract compliance for Omega Registry enrichment.
Compares entities in omega_registry.enriched.v1.json against required_keys in omega_registry_master.output_contract.yaml.
Emits canonical/logs/audit/contract_compliance/contract_compliance_report.json.

Usage:
    python -m scripts.audit.audit_contract_compliance

Ensure you run this from the workspace root so that all imports resolve correctly.
"""
import json
import os

from scripts.utils.import_path import set_workspace_root

set_workspace_root(__file__)
from scripts.utils.loaders import load_yaml
from scripts.utils.logging import attach_meta, write_json_log

ENRICHED_PATH = "canonical/omega_registry.enriched.v1.json"
CONTRACT_PATH = "canonical/support/contracts/omega_registry_master.output_contract.yaml"
REPORT_PATH = "canonical/logs/audit/contract_compliance/contract_compliance_report.json"
os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)

# Use canonical loader for contract YAML


def load_required_keys(contract_path):
    contract = load_yaml(contract_path)
    return contract.get("required_keys", [])


# Use standard JSON loader


def load_entities(enriched_path):
    with open(enriched_path) as f:
        return json.load(f)


def audit_entity(entity, required_keys):
    missing = []
    inferred = []
    trace = {}
    meta = entity.get("_meta", {})
    inferred_fields = meta.get("inferred_fields", {})
    for field in required_keys:
        value = entity.get(field)
        if value in [None, "", "null"]:
            missing.append(field)
            if inferred_fields.get(field, {}).get("join_origin") == "inferred":
                inferred.append(field)
            trace[field] = inferred_fields.get(field, {})
    # Enrich: Add optional contract validation (confidence, join_origin, etc.)
    contract_checks = {}
    # Example: confidence range check
    if "join_confidence" in entity:
        jc = entity["join_confidence"]
        contract_checks["join_confidence_valid"] = (
            isinstance(jc, (int, float)) and 0.75 <= jc <= 1.0
        )
    # Example: must_have_join_origin
    contract_checks["has_join_origin"] = bool(entity.get("join_origin"))
    # Example: area_id must not be null if device_id is present
    if entity.get("device_id") is not None:
        contract_checks["area_id_present_if_device_id"] = (
            entity.get("area_id") is not None
        )
    # Example: exposed_to_assistant must be boolean if present
    if "exposed_to_assistant" in entity:
        contract_checks["exposed_to_assistant_is_bool"] = isinstance(
            entity["exposed_to_assistant"], bool
        )
    return {
        "entity_id": entity.get("entity_id"),
        "missing_required_fields": missing,
        "fields_inferred": inferred,
        "join_health_score": meta.get("join_health_score", None),
        "trace_log": trace,
        "contract_checks": contract_checks,
    }


def main():
    required_keys = load_required_keys(CONTRACT_PATH)
    entities = load_entities(ENRICHED_PATH)
    report = [audit_entity(e, required_keys) for e in entities]
    # Attach meta and write using shared logging utility
    meta = attach_meta(
        source_script="audit_contract_compliance.py",
        contract_tag=CONTRACT_PATH,
        pipeline_stage="contract_audit",
    )
    write_json_log(REPORT_PATH, report, mode="w", meta=meta)
    print(f"Contract compliance report written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
