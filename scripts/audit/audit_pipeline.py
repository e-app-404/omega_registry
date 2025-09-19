#!/usr/bin/env python3
# Run with: python -m scripts.audit.audit_pipeline
"""
Audit pipeline for Omega Registry.
Emits real-data audit artifacts and logs all actions for full lineage tracking.
"""
# PATCH PATCH-AUDIT-FILE-REALDATA-V1
# Action: Extract real audit data from omega_registry_master.json and emit populated audit files
# Timestamp: 2025-07-22T16:45:00Z

import hashlib
import json
import os
from datetime import datetime, timezone

REGISTRY_PATH = "canonical/omega_registry_master.json"
AUDIT_DIR = "canonical/logs/audit/audit_pipeline/"
os.makedirs(AUDIT_DIR, exist_ok=True)


def emit_tier_assignment_report(registry, now, outdir):
    assignments = []
    for e in registry:
        assignments.append(
            {
                "entity_id": e.get("entity_id"),
                "tier": e.get("tier", "?"),
                "inference": e.get("field_inheritance", {}).get("tier", "?"),
                "fallback": "?" if e.get("tier", "?") == "?" else "",
            }
        )
    tier_summary = {
        "summary": f"Tier assignment audit for omega_registry_master.json. Total entities: {len(assignments)}.",
        "details": assignments,
        "timestamp": now,
    }
    with open(f"{outdir}tier_assignment_report.json", "w") as f:
        json.dump(tier_summary, f, indent=2)
    return f"{outdir}tier_assignment_report.json"


def emit_field_population_audit(registry, now, outdir):
    fields = ["domain", "tier", "device_class", "area_id", "room_ref", "floor_id"]
    field_stats = {}
    total = len(registry)
    for field in fields:
        non_null = sum(1 for e in registry if e.get(field) not in [None, "", []])
        field_stats[field] = {
            "non_null": non_null,
            "total": total,
            "completeness": round(non_null / total, 4) if total else 0.0,
        }
    field_population = {"field_stats": field_stats, "timestamp": now}
    with open(f"{outdir}field_population_audit.json", "w") as f:
        json.dump(field_population, f, indent=2)
    return f"{outdir}field_population_audit.json", field_stats


def emit_regression_inspection_summary(registry, now, outdir, field_stats):
    sha256 = hashlib.sha256(json.dumps(registry, sort_keys=True).encode()).hexdigest()
    total = len(registry)
    tier_breakdown = {
        t: sum(1 for e in registry if e.get("tier") == t)
        for t in set(e.get("tier", "?") for e in registry)
    }
    verdict = (
        "pass"
        if field_stats["domain"]["completeness"] >= 0.9
        and tier_breakdown.get("?", 0) < total
        else "fail"
    )
    reasons = []
    if field_stats["domain"]["completeness"] < 0.9:
        reasons.append("Domain completeness below 90%.")
    if tier_breakdown.get("?", 0) == total:
        reasons.append("All entities have unresolved tier assignments.")
    regression_summary = {
        "summary": f"Regression inspection for omega_registry_master.json at {now}",
        "tier_breakdown": tier_breakdown,
        "field_population_stats": field_stats,
        "registry_sha256": sha256,
        "timestamp": now,
        "verdict": verdict,
        "reasons": reasons,
    }
    with open(f"{outdir}regression_inspection_summary.json", "w") as f:
        json.dump(regression_summary, f, indent=2)
    return (
        f"{outdir}regression_inspection_summary.json",
        sha256,
        verdict,
        reasons,
        total,
    )


if __name__ == "__main__":
    with open(REGISTRY_PATH) as f:
        registry = json.load(f)
    now = datetime.now(timezone.utc).isoformat()
    os.makedirs(AUDIT_DIR, exist_ok=True)
    tier_path = emit_tier_assignment_report(registry, now, AUDIT_DIR)
    field_path, field_stats = emit_field_population_audit(registry, now, AUDIT_DIR)
    regression_path, sha256, verdict, reasons, total = (
        emit_regression_inspection_summary(registry, now, AUDIT_DIR, field_stats)
    )
    # Log actions to PATCH PATCH-AUDIT-FILE-REALDATA-V1
    with open(
        "canonical/logs/scratch/COPILOT PATCH BLOCK: PATCH-AUDIT-FILE-REALDATA-V1.log",
        "a",
    ) as log:
        log.write(
            f"[{now}] Emitted tier_assignment_report.json, field_population_audit.json, regression_inspection_summary.json to {AUDIT_DIR}\n"
        )
        log.write(
            f"[{now}] SHA256: {sha256}, Total entities: {total}, Domain completeness: {field_stats['domain']['completeness']}\n"
        )
        log.write(f"[{now}] Verdict: {verdict}, Reasons: {reasons}\n")
        log.write(
            f"[{now}] Artifact paths: {tier_path}, {field_path}, {regression_path}\n"
        )
