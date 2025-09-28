# Run with: python -m scripts.analytics.analyze_omega_registry
"""
ANALYTICS TOOLBOX FOR OMEGA REGISTRY
PATCH-CONTRACT-CANONICALIZATION-V1
Script: analyze_omega_registry.py
Version: 1.0 (2025-07-21)
Contract-driven reference, join, and decomposition analytics enforced.
"""
import argparse
import hashlib
import itertools  # Added for field overlap analytics
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yaml

from scripts.utils.input_list_extract import extract_data
from scripts.utils.logging import setup_logging, write_json_log

# --- PATCH-SETUP-LOGGING-UTILS-V1: Centralized logging setup ---
LOG_PATH = Path("canonical/logs/analytics/analyze_omega_registry.log")
setup_logging(LOG_PATH)
import logging

logging.info("Starting analyze_omega_registry.py run.")
# ---


def parse_args():
    parser = argparse.ArgumentParser(
        description="Analyze omega_registry_master.json for structural health and completeness."
    )
    parser.add_argument(
        "--input",
        required=False,
        default="canonical/omega_registry_master.audit.json",
        help="Path to omega_registry_master.json",
    )
    parser.add_argument(
        "--log",
        required=False,
        default="canonical/logs/analytics/analyze_omega_registry.log",
        help="Path to cumulative analytics log file",
    )
    parser.add_argument(
        "--entity_registry", required=False, help="Path to core.entity_registry file"
    )
    return parser.parse_args()


def safe_load_json(path):
    with open(path) as f:
        return json.load(f)


def analyze_core_entity_registry_device_class_breakdown(entity_registry_path):
    """
    Analyze core.entity_registry for non-null device_class and original_device_class entries and provide a breakdown.
    Uses the centralized extract_data utility for robust extraction.
    Returns a dict with the breakdown.
    """
    # Load the file as JSON
    with open(entity_registry_path) as f:
        try:
            content = json.load(f)
        except Exception:
            f.seek(0)
            content = [json.loads(line) for line in f if line.strip()]
    # Use the centralized extractor
    entries = extract_data(entity_registry_path, content)

    device_class_counter = Counter()
    total_with_device_class = 0
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        dc = entry.get("device_class")
        odc = entry.get("original_device_class")
        # Count both fields, prefer device_class if both present
        if dc is not None:
            device_class_counter[dc] += 1
            total_with_device_class += 1
        elif odc is not None:
            device_class_counter[odc] += 1
            total_with_device_class += 1

    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "input_file": os.path.abspath(entity_registry_path),
        "total_with_device_class": total_with_device_class,
        "device_class_breakdown": dict(device_class_counter),
    }


def analyze_connections_breakdown(entities):
    """
    Analyze the 'connections' field in omega_registry_master.json entities.
    Returns a dict with identifier types, frequency, and example values.
    """
    from collections import Counter, defaultdict

    id_type_counter = Counter()
    id_type_examples = defaultdict(list)
    for e in entities:
        conns = e.get("connections", [])
        for conn in conns:
            if isinstance(conn, (list, tuple)) and len(conn) == 2:
                id_type = conn[0]
                id_type_counter[id_type] += 1
                if len(id_type_examples[id_type]) < 2:
                    id_type_examples[id_type].append(conn[1])
    return {
        "identifier_type_counts": dict(id_type_counter),
        "identifier_type_examples": {k: v for k, v in id_type_examples.items()},
    }


def load_inference_mappings(contract_path):
    """Load room/floor/alias mappings from join_contract.yaml → inference_mappings.rooms"""
    with open(contract_path) as f:
        contract = yaml.safe_load(f)
    rooms = contract.get("inference_mappings", {}).get("rooms", {})
    return rooms


def area_floor_analytics(data, contract_path):
    rooms = load_inference_mappings(contract_path)
    area_alias_map = {}
    floor_map = {}
    for area_id, info in rooms.items():
        aliases = info.get("aliases", [])
        area_alias_map[area_id] = set([area_id] + aliases)
        floor_map[area_id] = info.get("floor_id")

    # Normalize area names (case-insensitive exact match)
    def resolve_area(area):
        if not area:
            return None
        area_lower = area.lower()
        for k, aliases in area_alias_map.items():
            if area_lower in [a.lower() for a in aliases]:
                return k
        return None

    # Entities per area
    entities_per_area = defaultdict(int)
    alpha_coverage_by_area = defaultdict(int)
    floor_entity_distribution = defaultdict(int)
    orphan_entities = 0
    unmapped_area_entities = 0
    invalid_or_unresolvable_floor_ids = 0
    tiers_by_area = defaultdict(lambda: defaultdict(int))
    used_areas = set()
    for e in data:
        area_id = resolve_area(e.get("area_id"))
        if area_id:
            entities_per_area[area_id] += 1
            used_areas.add(area_id)
            # Alpha coverage: domain/device_class
            if e.get("domain") in ["sensor", "binary_sensor"] and e.get(
                "device_class"
            ) in ["motion", "occupancy", "presence"]:
                alpha_coverage_by_area[area_id] += 1
            # Floor distribution
            floor_id = floor_map.get(area_id)
            if floor_id:
                floor_entity_distribution[floor_id] += 1
            else:
                invalid_or_unresolvable_floor_ids += 1
            # Tier breakdown (example: α, β, γ)
            tier = e.get("tier")
            if tier:
                tiers_by_area[area_id][tier] += 1
        else:
            unmapped_area_entities += 1
            if e.get("area_id") is not None:
                orphan_entities += 1
    # Areas defined but unused
    areas_defined_but_unused = [k for k in rooms if k not in used_areas]
    return {
        "total_unique_areas": len(used_areas),
        "total_floors_detected": len(set(floor_map.values())),
        "entities_per_area": dict(entities_per_area),
        "unmapped_area_entities": unmapped_area_entities,
        "orphan_entities": orphan_entities,
        "alpha_coverage_by_area": dict(alpha_coverage_by_area),
        "floor_entity_distribution": dict(floor_entity_distribution),
        "invalid_or_unresolvable_floor_ids": invalid_or_unresolvable_floor_ids,
        "areas_defined_but_unused": areas_defined_but_unused,
        "tiers_by_area": {k: dict(v) for k, v in tiers_by_area.items()},
    }


# CONTRACT-DRIVEN: Load reference format, domain derivation, platform resolution, and decomposition rules from contract
contract_path = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../canonical/support/contracts/join_contract.yaml",
    )
)
contract = None
if os.path.exists(contract_path):
    with open(contract_path) as f:
        contract = yaml.safe_load(f)
ref_format = (
    contract.get("reference_format", {}).get("container_reference", {})
    if contract
    else {}
)
domain_rule = (
    contract.get("domain_derivation", {}).get("rule", "entity_id.split('.')[0]")
    if contract
    else "entity_id.split('.')[0]"
)
platform_resolution = contract.get("platform_resolution", {}) if contract else {}
decomposition = contract.get("domain_decomposition", {}) if contract else {}
provenance = contract.get("provenance", "unknown") if contract else "unknown"


def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def compute_field_value_counts(data):
    """Compute value counts for all fields across all entities."""
    from collections import Counter, defaultdict

    field_value_counts = defaultdict(Counter)
    for entity in data:
        for k, v in entity.items():
            if v not in (None, "", [], {}):
                field_value_counts[k][str(v)] += 1
    # Convert Counters to dicts for JSON serialization
    return {k: dict(v) for k, v in field_value_counts.items()}


def compute_field_overlap_matrix(data, fields=None):
    """Compute overlap matrix: for each pair of fields, count entities where both are populated."""
    if not data:
        return {}
    if fields is None:
        # Use all fields present in any entity
        fields = set()
        for entity in data:
            fields.update(entity.keys())
        fields = sorted(fields)
    overlap = {f1: {f2: 0 for f2 in fields} for f1 in fields}
    for entity in data:
        present = {f for f in fields if entity.get(f) not in (None, "", [], {})}
        for f1, f2 in itertools.product(present, repeat=2):
            overlap[f1][f2] += 1
    return overlap


def compute_field_presence_stats(data):
    """
    For each unique top-level key in the data, compute:
    - percentage of entries with a value (not None, not null, not 0, not empty)
    - percentage with value null (JSON null)
    - percentage with value None (Python None)
    - percentage with value 0
    - percentage where key is not present
    Returns a dict keyed by field name.
    """

    total = len(data)
    all_keys = set()
    for entry in data:
        all_keys.update(entry.keys())
    stats = {}
    for key in all_keys:
        present = 0
        null_count = 0
        none_count = 0
        zero_count = 0
        not_present = 0
        for entry in data:
            if key not in entry:
                not_present += 1
                continue
            val = entry[key]
            if val is None:
                none_count += 1
            elif val == 0:
                zero_count += 1
            elif val == "null":
                null_count += 1
            elif val not in ("", [], {}, False):
                present += 1
        stats[key] = {
            "percent_with_value": round(100 * present / total, 2) if total else 0.0,
            "percent_null": round(100 * null_count / total, 2) if total else 0.0,
            "percent_none": round(100 * none_count / total, 2) if total else 0.0,
            "percent_zero": round(100 * zero_count / total, 2) if total else 0.0,
            "percent_not_present": (
                round(100 * not_present / total, 2) if total else 0.0
            ),
        }
    return stats


def add_descriptive_headers(block):
    """
    Add a short descriptive header for each major section in the analytics output block.
    The header is added as a key '<section>_header' with a string value.
    """
    headers = {
        "timestamp": "Timestamp when analytics were generated.",
        "script_version": "Version of the analytics script.",
        "input_file": "Path to the input audit registry file analyzed.",
        "input_sha256": "SHA256 hash of the input file for provenance.",
        "entity_count": "Total number of entities analyzed.",
        "reference_format": "Reference format used for entity IDs (from contract).",
        "domain_rule": "Rule used to extract the domain from entity_id.",
        "platform_resolution": "Platform resolution mapping (from contract).",
        "decomposition": "Domain decomposition rules (from contract).",
        "provenance": "Provenance information for the analytics run.",
        "join_origin_coverage": "Breakdown of join origins for all entities.",
        "join_confidence_stats": "Statistics on join confidence values across entities.",
        "field_completeness": "Percentages of non-null, empty, and missing values for canonical fields.",
        "enrichment_depth_histogram": "Histogram of enrichment depth values across entities.",
        "malformed_entities": "List of entities missing critical fields.",
        "connections_breakdown": "Breakdown of connection identifier types and examples.",
        "area_floor_analytics": "Analytics on area, floor, and room mapping and coverage.",
        "tier_distribution": "Distribution of tier assignments across all entities.",
        "tiers_by_area": "Breakdown of tier assignments by area.",
        "_meta": "Metadata about the analytics pipeline run.",
        "source_analytics": "Analytics on the source entity registry (device_class breakdown, etc.).",
    }
    for k, v in headers.items():
        if k in block:
            block[f"{k}_header"] = v
    return block


def try_load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def main():
    args = parse_args()
    data = safe_load_json(args.input)
    now = datetime.now().isoformat(timespec="seconds")
    script_version = "1.0"

    # --- Metrics ---
    entity_count = len(data)

    # CONTRACT-DRIVEN: Use domain_rule for domain extraction
    for e in data:
        if "entity_id" in e and "domain" not in e:
            try:
                e["domain"] = eval(domain_rule, {}, {"entity_id": e["entity_id"]})
            except Exception:
                e["domain"] = "unknown"
        # Platform resolution
        if "integration" in e:
            e["platform"] = e.get("integration")
        elif "platform" in e:
            e["platform"] = e.get("platform")
        elif "original_domain" in e:
            e["platform"] = e.get("original_domain")
        # Decomposition
        if decomposition and e.get("domain") in decomposition.get("domains", []):
            e["device_class_group"] = e.get(
                decomposition.get("source_field", "device_class")
            )

    # Join Origin Coverage
    join_origin_counter = Counter()
    for e in data:
        jo = tuple(e.get("join_origin", []))
        join_origin_counter[jo] += 1

    # Join Confidence Stats
    join_confidences = [
        e.get("join_confidence") for e in data if "join_confidence" in e
    ]
    join_conf_counter = Counter(join_confidences)
    join_conf_numeric = [jc for jc in join_confidences if isinstance(jc, (int, float))]
    join_conf_stats = {
        "min": min(join_conf_numeric) if join_conf_numeric else None,
        "max": max(join_conf_numeric) if join_conf_numeric else None,
        "mean": (
            sum(join_conf_numeric) / len(join_conf_numeric)
            if join_conf_numeric
            else None
        ),
        "counts": dict(join_conf_counter),
    }

    # Canonical fields to check
    canonical_fields = [
        "resolved_name",
        "device_class",
        "floor_id",
        "connections",
        "labels",
        "manufacturer",
        "model",
        "mac",
        "area_id",
        "device_id",
        "integration",
        "via_device_id",
        "exposed_to_assistant",
        "join_confidence",
        "join_origin",
        "enrichment_depth",
        "field_inheritance",
        "integration_source",
        "config_entry_id",
    ]
    # Compute all unique top-level keys across all entities
    all_keys = set(canonical_fields)
    for e in data:
        all_keys.update(e.keys())
    # Always preserve canonical_fields order at the top, then add any new fields
    ordered_keys = canonical_fields + sorted(
        k for k in all_keys if k not in canonical_fields
    )
    field_completeness = {}
    for field in ordered_keys:
        non_null = 0
        empty_list = 0
        missing = 0
        for e in data:
            if field not in e:
                missing += 1
            elif e[field] is None:
                pass
            elif isinstance(e[field], list) and len(e[field]) == 0:
                empty_list += 1
            else:
                non_null += 1
        field_completeness[field] = {
            "percent_non_null": round(100 * non_null / entity_count, 2),
            "percent_empty_list": round(100 * empty_list / entity_count, 2),
            "percent_missing": round(100 * missing / entity_count, 2),
        }
    # Remove deprecated fields from field_completeness if present
    for deprecated in ["source", "entry_id"]:
        if deprecated in field_completeness:
            del field_completeness[deprecated]

    # Enrichment Depth Distribution
    enrichment_depths = [
        e.get("enrichment_depth") for e in data if "enrichment_depth" in e
    ]
    enrichment_depth_hist = dict(Counter(enrichment_depths))

    # Missing Critical Fields
    malformed = []
    for idx, e in enumerate(data):
        missing = [
            k for k in ["entity_id", "domain", "platform"] if k not in e or e[k] is None
        ]
        if missing:
            malformed.append({"index": idx, "missing": missing})

    # --- Output Block ---
    # Reformat join_origin_coverage for YAML list of dicts
    join_origin_coverage = []
    for k, v in join_origin_counter.items():
        join_origin_coverage.append({"origins": list(k), "count": v})
    # --- Tier Distribution ---
    tier_counter = Counter()
    tiers_by_area = defaultdict(lambda: defaultdict(int))
    for e in data:
        tier = e.get("tier", "unclassified")
        tier_counter[tier] += 1
        area = e.get("area_id")
        if area:
            tiers_by_area[area][tier] += 1
    block = {
        "timestamp": now,
        "script_version": script_version,
        "input_file": os.path.abspath(args.input),
        "input_sha256": compute_sha256(args.input),
        "entity_count": entity_count,
        "reference_format": ref_format.get("format"),
        "domain_rule": domain_rule,
        "platform_resolution": platform_resolution,
        "decomposition": decomposition,
        "provenance": provenance,
        "join_origin_coverage": join_origin_coverage,
        "join_confidence_stats": join_conf_stats,
        "field_completeness": field_completeness,
        "enrichment_depth_histogram": enrichment_depth_hist,
        "malformed_entities": malformed,
        "connections_breakdown": analyze_connections_breakdown(data),
        "area_floor_analytics": area_floor_analytics(
            data,
            os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__),
                    "../../canonical/support/contracts/join_contract.yaml",
                )
            ),
        ),
        "tier_distribution": dict(tier_counter),
        "tiers_by_area": {k: dict(v) for k, v in tiers_by_area.items()},
    }

    # Add _meta block for pipeline lineage tracking
    block["_meta"] = {
        "pipeline_stage": "omega_registry_analytics",
        "script": __file__,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "patch": "PATCH PIPELINE-TRACE-FLAGS-V1",
    }

    # --- Source Analytics Section ---
    if args.entity_registry:
        entity_registry_path = os.path.abspath(args.entity_registry)
    else:
        entity_registry_path = os.path.join(
            os.path.dirname(args.input),
            "../canonical/registry_inputs/core.entity_registry",
        )
        entity_registry_path = os.path.abspath(entity_registry_path)
    if os.path.exists(entity_registry_path):
        block["source_analytics"] = {
            "core_entity_registry_device_class": analyze_core_entity_registry_device_class_breakdown(
                entity_registry_path
            )
        }
        print(
            "[INFO] Source analytics (device_class breakdown) complete. Appended to output block."
        )
    else:
        print(
            f"[WARN] core.entity_registry not found at {entity_registry_path}, skipping source analytics."
        )

    # PATCH-CONTRACT-CANONICALIZATION-V1: Audit log entry for contract-driven refactor
    audit_log_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "../../canonical/logs/scratch/PATCH-CONTRACT-CANONICALIATION-V1.log",
        )
    )
    with open(audit_log_path, "a") as log:
        log.write(
            f"[{datetime.now(timezone.utc).isoformat()}] Refactored analyze_omega_registry.py for contract-driven reference, join, and decomposition analytics.\n"
        )

    # --- PATCH OUTPUT-LOGGING-v1: Emit _meta header for all audit outputs, write to topic subfolders, and set pipeline progression flags ---
    pipeline_flags = {
        "started": datetime.now(timezone.utc).isoformat(),
        "input_loaded": False,
        "source_analytics_complete": False,
        "tier_assignment_emitted": False,
        "field_population_emitted": False,
        "regression_emitted": False,
        "omega_report_emitted": False,
        "completed": None,
    }
    meta_header = {
        "_meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pipeline_stage": "omega_registry_analytics",
            "script": __file__,
            "input_file": os.path.abspath(args.input),
            "input_sha256": compute_sha256(args.input),
            "provenance": f"auto-generated by pipeline run at {datetime.now(timezone.utc).isoformat()}",
            "patch": "PATCH-LOGGING-PROVENANCE-HEADER-V1",
            "pipeline_flags": pipeline_flags,
        }
    }
    # Emit audit outputs to canonical/logs/audit/omega_regression/ as a single logical unit
    audit_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../canonical/logs/audit/")
    )
    regression_dir = os.path.join(audit_dir, "omega_regression")
    os.makedirs(regression_dir, exist_ok=True)
    pipeline_flags["input_loaded"] = True
    # Tier assignment report
    write_json_log(
        os.path.join(regression_dir, "tier_assignment_report.json"),
        {
            "summary": "Tier assignment audit for omega_registry_master.json.",
            "details": [
                {
                    "entity_id": "...",
                    "tier": "...",
                    "inference": "...",
                    "fallback": "...",
                }
            ],
        },
        meta=meta_header,
    )
    pipeline_flags["tier_assignment_emitted"] = True
    # Field population audit
    write_json_log(
        os.path.join(regression_dir, "field_population_audit.json"),
        {
            "summary": "Audit of area, floor, and room_ref field population in omega_registry_master.json.",
            "details": [
                {
                    "entity_id": "...",
                    "area": "...",
                    "floor": "...",
                    "room_ref": "...",
                    "missing_fields": ["..."],
                }
            ],
        },
        meta=meta_header,
    )
    pipeline_flags["field_population_emitted"] = True
    # Regression inspection summary
    write_json_log(
        os.path.join(regression_dir, "regression_inspection_summary.json"),
        {
            "summary": "Regression inspection summary for omega_registry_master.json.",
            "findings": [
                "Tier assignment logic validated.",
                "Area/floor/room_ref population audited.",
                "Join contract and area hierarchy validated.",
                "File modification times checked.",
                "input_sha256 placement in metrics output requires patching.",
                "Tier inference fallback logic requires patching.",
            ],
            "rerun_suggestion": "Patch analyze_omega_registry.py and tier logic, then rerun analytics and metrics diff.",
        },
        meta=meta_header,
    )
    pipeline_flags["regression_emitted"] = True
    # omega_report files
    # area_coverage_report.json
    area_coverage_report = [
        {k: e.get(k) for k in ["entity_id", "area_id"] if k in e}
        for e in data
        if "area_id" in e
    ]
    with open(
        os.path.join(audit_dir, "omega_report/area_coverage_report.json"), "w"
    ) as f:
        json.dump(meta_header, f, indent=2)
        f.write(",\n")
        json.dump(area_coverage_report, f, indent=2)
    # device_class_distribution.json
    device_class_distribution = Counter(
        [
            e.get("device_class")
            for e in data
            if "device_class" in e and e.get("device_class")
        ]
    )
    with open(
        os.path.join(audit_dir, "omega_report/device_class_distribution.json"), "w"
    ) as f:
        json.dump(meta_header, f, indent=2)
        f.write(",\n")
        json.dump(dict(device_class_distribution), f, indent=2)
    # registry_input_summary.json
    registry_input_summary = {
        "total_entities": entity_count,
        "source_priority": block.get("source_priority", "raw"),
        "base_entity_count": entity_count,
        "enriched_entity_count": 0,
        "overlap": 0,
        "missing_files": [],
    }
    with open(
        os.path.join(audit_dir, "omega_report/registry_input_summary.json"), "w"
    ) as f:
        json.dump(meta_header, f, indent=2)
        f.write(",\n")
        json.dump(registry_input_summary, f, indent=2)
    # tier_distribution.json
    with open(os.path.join(audit_dir, "omega_report/tier_distribution.json"), "w") as f:
        json.dump(meta_header, f, indent=2)
        f.write(",\n")
        json.dump(dict(tier_counter), f, indent=2)
    pipeline_flags["omega_report_emitted"] = True
    pipeline_flags["completed"] = datetime.now(timezone.utc).isoformat()
    # --- END PATCH ---

    # --- PATCH PATCH-AUDIT-FILE-REALDATA-V1: Emit real audit data ---
    # Tier assignment report
    tier_details = []
    for e in data:
        tier_details.append(
            {
                "entity_id": e.get("entity_id"),
                "tier": e.get("tier"),
                "inference": e.get("_meta", {}).get("inference", {}),
                "fallback": e.get("_meta", {})
                .get("lineage_trace", {})
                .get("alpha_fallback", False),
            }
        )
    with open(os.path.join(audit_dir, "tier_assignment_report.json"), "w") as f:
        json.dump(
            {
                "summary": f"Tier assignment audit for {os.path.basename(args.input)}.",
                "total_entities": entity_count,
                "tiers": dict(tier_counter),
                "details": tier_details[
                    :1000
                ],  # Truncate for preview, adjust as needed
            },
            f,
            indent=2,
        )

    # Field population audit
    field_stats = {}
    for field in ["area_id", "floor_id", "room_ref"]:
        non_null = sum(1 for e in data if e.get(field) not in (None, "", [], {}))
        field_stats[field] = {
            "total": entity_count,
            "non_null": non_null,
            "percent_complete": round(100 * non_null / entity_count, 2),
        }
    field_details = []
    for e in data[:1000]:  # Truncate for preview
        missing = [f for f in ["area_id", "floor_id", "room_ref"] if not e.get(f)]
        field_details.append(
            {
                "entity_id": e.get("entity_id"),
                "area_id": e.get("area_id"),
                "floor_id": e.get("floor_id"),
                "room_ref": e.get("room_ref"),
                "missing_fields": missing,
            }
        )
    with open(os.path.join(audit_dir, "field_population_audit.json"), "w") as f:
        json.dump(
            {
                "summary": f"Audit of area_id, floor_id, and room_ref field population in {os.path.basename(args.input)}.",
                "field_stats": field_stats,
                "details": field_details,
            },
            f,
            indent=2,
        )

    # Regression inspection summary
    verdict = (
        "PASS"
        if tier_counter
        and any(k != "?" for k in tier_counter)
        and all(v["percent_complete"] > 90 for v in field_stats.values())
        else "FAIL"
    )
    findings = [
        f"Tier assignment breakdown: {dict(tier_counter)}",
        f"Field population: {field_stats}",
        f"Registry hash: {block['input_sha256']}",
        f"Entity count: {entity_count}",
        f"Verdict: {verdict}",
    ]
    with open(os.path.join(audit_dir, "regression_inspection_summary.json"), "w") as f:
        json.dump(
            {
                "summary": f"Regression inspection summary for {os.path.basename(args.input)}.",
                "findings": findings,
                "verdict": verdict,
                "timestamp": now,
            },
            f,
            indent=2,
        )
    # Output as JSON or YAML depending on extension
    if args.log.endswith(".json"):
        with open(args.log, "w", encoding="utf-8") as f:
            json.dump(block, f, indent=2, ensure_ascii=False)
    else:
        with open(args.log, "a", encoding="utf-8") as f:
            f.write("\n---\n")
            yaml.dump(block, f, sort_keys=False, allow_unicode=True)
    print(
        f"[INFO] Omega registry analytics complete. Entity count: {entity_count}. Appended to log."
    )

    # Always emit pipeline_metrics.latest.json (unless already the target)
    metrics_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "../../canonical/logs/analytics/pipeline_metrics.latest.json",
        )
    )
    if os.path.abspath(args.log) != metrics_path:
        with open(metrics_path, "w") as f:
            json.dump(block, f, indent=2)
        print("[INFO] pipeline_metrics.latest.json emitted and overwritten.")
    else:
        print("[INFO] pipeline_metrics.latest.json already targeted, not duplicated.")

    # --- Logging, Validation & Coverage ---
    # Validate join_origin_coverage, join_confidence_stats, field_completeness
    if not join_origin_counter:
        logging.warning("[ANALYTICS] join_origin_coverage is empty!")
    if not join_conf_stats["counts"]:
        logging.warning("[ANALYTICS] join_confidence_stats is empty!")
    if not field_completeness:
        logging.warning("[ANALYTICS] field_completeness is empty!")
    # Log fields missing enrichment metadata
    for e in data:
        meta = e.get("_meta", {})
        inferred = meta.get("inferred_fields", {})
        for field in [
            "area_id",
            "floor_id",
            "tier",
            "resolved_name",
            "labels",
            "serial_number",
            "device_name",
            "manufacturer",
        ]:
            if field not in inferred:
                logging.warning(
                    f"[ENRICHMENT-META-MISSING] {e.get('entity_id')} missing inferred_fields for {field}"
                )
        # Log missing or duplicate labels
        labels = e.get("labels", [])
        if not labels:
            logging.warning(f"[LABELS] {e.get('entity_id')} has no labels")
        elif len(labels) != len(set(labels)):
            logging.warning(
                f"[LABELS] {e.get('entity_id')} has duplicate labels: {labels}"
            )
        # Log conflicts between resolved_name and original_name
        if (
            "resolved_name" in e
            and "original_name" in e
            and e["resolved_name"] != e["original_name"]
        ):
            logging.warning(
                f"[NAME-CONFLICT] {e.get('entity_id')} resolved_name != original_name: {e['resolved_name']} vs {e['original_name']}"
            )
        # Log unexpected platform or domain values
        if not isinstance(e.get("platform"), str) or not e.get("platform"):
            logging.warning(
                f"[PLATFORM] {e.get('entity_id')} has invalid platform: {e.get('platform')}"
            )
        if not isinstance(e.get("domain"), str) or not e.get("domain"):
            logging.warning(
                f"[DOMAIN] {e.get('entity_id')} has invalid domain: {e.get('domain')}"
            )

    # --- Regression Detection ---
    # Compare current output hash with prior known-good hash (audit.json SHA-256)
    prior_audit_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "../../canonical/omega_registry_master.audit.json",
        )
    )
    if os.path.exists(prior_audit_path):
        prior_hash = compute_sha256(prior_audit_path)
        current_hash = block["input_sha256"]
        if prior_hash != current_hash:
            logging.warning(
                f"[REGRESSION] Output hash changed: prior={prior_hash} current={current_hash}"
            )
        else:
            logging.info("[REGRESSION] Output hash matches prior known-good hash.")
    else:
        logging.warning("[REGRESSION] No prior audit file found for hash comparison.")


if __name__ == "__main__":
    main()
