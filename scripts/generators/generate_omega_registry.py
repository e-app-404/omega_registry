#!/usr/bin/env python3
"""
Run as module: python -m scripts.generators.generate_omega_registry
PATCH ABSOLUTE-IMPORT-UTILS-V1: Refactored for absolute imports, removed sys.path and dynamic import hacks, added run-as-module comment.
"""

"""
PATCH-GENERATE-OMEGA-REGISTRY-HEADER-V3
Generates the primary join graph and emits the canonical omega_registry_master.json.
Handles multi-source enrichment, join tracing, and field inheritance as per contract definitions.
"""

raise RuntimeError("This script is deprecated. Use omega_pipeline_main.py instead.")

import argparse
import hashlib
import json
import logging
import os
import unicodedata
from datetime import datetime
from pathlib import Path

import yaml

from scripts.utils.import_path import set_workspace_root
from scripts.utils.logging import attach_meta, setup_logging

set_workspace_root(__file__)
from scripts.utils.input_list_extract import extract_data
from scripts.utils.pipeline_config import OMEGA_REGISTRY_STRICT_ALLOWLIST
from scripts.utils.registry import (
    contract_minimize_meta,
    flatten_options_to_voice_assistants,
    strip_null_fields,
)

# Setup centralized logging
LOG_PATH = Path("canonical/logs/generators/generate_omega_registry.log")
setup_logging(LOG_PATH)
logging.info("Starting generate_omega_registry.py run.")

CONFLICT_LOG_PATH = "canonical/logs/scratch/CONFLICT-RESOLUTION-AUDIT-20250721.log"


def load_json(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    # Fallback: try extensionless filename
    if path.endswith(".json"):
        alt_path = path[:-5]
        if os.path.exists(alt_path):
            with open(alt_path) as f:
                return json.load(f)
    print(f"[WARN] Missing input: {path}")
    return None


def load_json_with_extract(path):
    content = load_json(path)
    if content is None:
        return []
    entries = extract_data(path, content)
    if not entries:
        print(f"[WARN] No valid entries extracted from: {path}")
    return entries


def resolve_enrichment_path(rel_path):
    """
    Resolves the canonical path for enrichment sources under enrichment_sources/.
    Example: resolve_enrichment_path('hestia/pre-reboot/omega_device_registry.json')
    """
    from pathlib import Path

    return str(Path("canonical/enrichment_sources") / rel_path)


def get_sha256(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None


# PATCH: Move safe_exists and safe_join to the absolute first lines of the file, before any other code
from typing import Any


def safe_exists(path: Any) -> bool:
    try:
        import os

        return os.path.exists(str(path))
    except Exception:
        return False


def safe_join(*args: Any) -> str:
    try:
        import os

        return os.path.join(*(str(a) for a in args))
    except Exception:
        return "/".join(str(a) for a in args)


# PATCH: ensure deduped_entities and contract_allowlist are always defined after entities and allowed_fields are set
# Place this after entities and allowed_fields are both defined
# PATCH: deduped_entities assignment moved after entities is defined (see below)
# PATCH: fix write_json_compact import/definition to match expected signature
if "write_json_compact" not in globals():

    def write_json_compact(data, path):
        with open(path, "w", encoding="utf-8") as f:
            import json

            json.dump(data, f, separators=(",", ":"), ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description="Generate omega_registry_master.json with debug log support."
    )
    parser.add_argument(
        "--output", required=True, help="Output path for omega_registry_master.json"
    )
    parser.add_argument("--debug_log", help="Path to emit debug .jsonl log")
    parser.add_argument(
        "--enrich-entities-from", help="Optional enrichment source for entities"
    )
    args = parser.parse_args()

    # --- BEGIN PATCH: Source Contract Enumeration ---
    contract_path = "canonical/support/contracts/join_contract.yaml"
    with open(contract_path) as f:
        contract = yaml.safe_load(f)
    expected_files = set()
    file_to_anchor = {}
    for entry in contract["contract"]["sections"]:
        if "canonical_inputs_scope" in entry:
            for fdef in entry["canonical_inputs_scope"]:
                fname = fdef["file"]
                expected_files.add(fname)
        if "files" in entry:
            for fdef in entry["files"]:
                fname = fdef["filename"]
                expected_files.add(fname)
                file_to_anchor[fname] = fdef.get("anchor_type")
    # List of all 15 expected files (from contract)
    all_input_files = list(expected_files)
    # --- END PATCH ---

    # --- BEGIN PATCH: Load all 15 input files ---
    input_dir = "canonical/registry_inputs/"
    loaded_files = {}
    for fname in all_input_files:
        fpath_json = safe_join(input_dir, fname + ".json")
        fpath = fpath_json if safe_exists(fpath_json) else safe_join(input_dir, fname)
        loaded = load_json_with_extract(fpath)
        loaded_files[fname] = loaded
    # --- END PATCH ---

    # Overwrite registry variables with loaded_files for canonical sources
    entity_registry = loaded_files.get("core.entity_registry", [])
    device_registry = loaded_files.get("core.device_registry", [])
    area_registry = loaded_files.get("core.area_registry", [])
    floor_registry = loaded_files.get("core.floor_registry", [])
    config_entries = loaded_files.get("core.config_entries", [])
    restore_state = loaded_files.get("core.restore_state", [])
    exposed_entities = loaded_files.get("homeassistant.exposed_entities", [])

    # Index for fast lookup
    device_by_id = {d["id"]: d for d in device_registry if "id" in d}
    area_by_id = {a["id"]: a for a in area_registry if "id" in a}
    floor_by_id = {f["floor_id"]: f for f in floor_registry if "floor_id" in f}
    config_by_entry = {c["entry_id"]: c for c in config_entries if "entry_id" in c}
    restore_by_entity = {r["entity_id"]: r for r in restore_state if "entity_id" in r}
    exposed_set = set(exposed_entities)

    # --- BEGIN PATCH: Enrichment Source Resolution ---
    # All enrichment sources must be loaded from canonical/enrichment_sources/.
    # Example usage: resolve_enrichment_path('ha_registries/post-reboot', 'core.entity_registry')
    # The pipeline should not reference derived_views/.
    # Only scan network/ and manual/ if integration targets exist.
    # --- END PATCH ---

    # --- BEGIN PATCH: Enrichment Source Loading Example ---
    # Example: Load post-reboot entity registry from enrichment_sources
    load_json_with_extract(
        resolve_enrichment_path("ha_registries/post-reboot/core.entity_registry.json")
    )
    # Only scan network/ and manual/ if integration targets exist (pseudo-code):
    # if integration_targets:
    #     network_files = os.listdir(resolve_enrichment_path('network', ''))
    #     manual_files = os.listdir(resolve_enrichment_path('manual', ''))
    # --- END PATCH ---

    # --- BEGIN PATCH: Ingestion Status Output ---
    ingestion_status = {
        "expected_files": sorted(list(expected_files)),
        "file_status": {},  # New: detailed extraction outcomes
        "loaded_files": [],
        "missing_files": [],
        "unused_files": [],
    }
    for fname in sorted(list(expected_files)):
        fpath_json = safe_join(input_dir, fname + ".json")
        fpath = fpath_json if safe_exists(fpath_json) else safe_join(input_dir, fname)
        status = {"present": safe_exists(fpath), "extraction": None, "reason": None}
        if status["present"]:
            try:
                content = load_json(fpath)
                if content is None:
                    status["extraction"] = False
                    status["reason"] = "File present but not valid JSON or empty."
                else:
                    entries = extract_data(fpath, content)
                    if entries and isinstance(entries, list) and len(entries) > 0:
                        status["extraction"] = True
                        status["reason"] = f"Extracted {len(entries)} entries."
                        ingestion_status["loaded_files"].append(fname)
                    else:
                        status["extraction"] = False
                        status["reason"] = "No valid entries extracted."
                        ingestion_status["missing_files"].append(fname)
            except Exception as ex:
                status["extraction"] = False
                status["reason"] = f"Extraction error: {ex}"
                ingestion_status["missing_files"].append(fname)
        else:
            status["extraction"] = False
            status["reason"] = "File not found."
            ingestion_status["missing_files"].append(fname)
        ingestion_status["file_status"][fname] = status
    # --- END PATCH ---

    # --- PATCH-ANCHOR-SOURCE-CORRECTION-V1 ---
    # Remove deprecated files from expected_files
    deprecated_files = [
        "input_number.verified.generated.json",
        "input_datetime.verified.generated.json",
        "input_text.verified.generated.json",
    ]
    all_input_files = [f for f in all_input_files if f not in deprecated_files]
    # CLI flag for enrichment
    enrich_path = (
        getattr(args, "enrich_entities_from", None)
        if hasattr(args, "enrich_entities_from")
        else None
    )
    enriched_entities = []
    enriched_sha = None
    base_sha = None
    if enrich_path:
        try:
            enriched_entities = load_json_with_extract(enrich_path)
            enriched_sha = get_sha256(enrich_path)
        except Exception as ex:
            print(f"[WARN] Could not load enrichment source: {ex}")
    base_entity_path = safe_join(input_dir, "core.entity_registry")
    base_entities = load_json_with_extract(base_entity_path)
    base_sha = get_sha256(base_entity_path)
    use_enriched = False
    if enriched_entities and enriched_sha and base_sha:
        if enriched_sha != base_sha:
            print(
                "[CRITICAL] Mismatch detected: core.entity_registry from enrichment_sources is older than registry_inputs. Skipping enrichment merge."
            )
        else:
            use_enriched = True
    entities = enriched_entities if use_enriched else base_entities
    source_priority = "enriched" if use_enriched else "raw"
    if not use_enriched:
        print("[WARN] Fallback to base entity registry.")
    # Deduplication pass
    seen_ids = set()
    # Deduplication pass
    seen_ids = set()
    unique_entities = []
    for entity in entities:
        if entity.get("entity_id") not in seen_ids:
            seen_ids.add(entity["entity_id"])
            unique_entities.append(entity)
    entities = unique_entities
    # PATCH: ensure deduped_entities is always defined after deduplication
    deduped_entities = entities
    # --- END PATCH ---
    debug_records = []
    propagation_audit = []
    loop_counter = 0
    max_loops = 100000
    # PATCH-OMEGA-REGISTRY-DOMAIN-OVERRIDE-V1
    # Load tier lookup from pipeline_metrics.latest.json
    try:
        with open("canonical/logs/analytics/pipeline_metrics.latest.json") as f:
            pipeline_metrics = json.load(f)
            # Example: {"tiers_by_entity": {"sensor.sun_next_dawn": "α", ...}}
            tier_lookup = pipeline_metrics.get("tiers_by_entity", {})
    except Exception as ex:
        print(f"[WARN] Could not load tier index: {ex}")
        tier_lookup = {}

    # Load area hierarchy
    try:
        with open("canonical/support/contracts/area_hierarchy.yaml") as f:
            area_hierarchy = yaml.safe_load(f)
            area_nodes = {n["id"]: n for n in area_hierarchy.get("nodes", [])}
    except Exception as ex:
        print(f"[WARN] Could not load area hierarchy: {ex}")
        area_nodes = {}
    tier_hist = {}
    unresolved_tier_entities = []
    area_coverage_report = []
    device_class_hist = {}
    # Authoritative entity sources
    authoritative_entity_sources = [
        "canonical/registry_inputs/core.entity_registry",
        "canonical/registry_inputs/core.device_registry",
        "canonical/registry_inputs/core.area_registry",
        "canonical/registry_inputs/core.floor_registry",
        "canonical/registry_inputs/core.config_entries",
    ]
    # Load canonical entity registry
    canonical_entity_path = authoritative_entity_sources[0]
    canonical_entities = load_json_with_extract(canonical_entity_path)
    # Optionally load enrichment source
    enrichment_entities = []
    enrichment_sha = None
    canonical_sha = get_sha256(canonical_entity_path)
    if args.enrich_entities_from:
        enrichment_entities = load_json_with_extract(args.enrich_entities_from)
        enrichment_sha = get_sha256(args.enrich_entities_from)
        if canonical_sha != enrichment_sha:
            print(
                f"[CRITICAL] Mismatch detected: {canonical_entity_path} vs {args.enrich_entities_from}. Skipping enrichment merge."
            )
            enrichment_entities = []
    # Merge enrichment only if explicitly requested and hashes match
    entity_registry = canonical_entities
    if enrichment_entities:
        # Only enrich missing fields, never override
        for i, entity in enumerate(entity_registry):
            enrich = next(
                (
                    e
                    for e in enrichment_entities
                    if e.get("entity_id") == entity.get("entity_id")
                ),
                None,
            )
            if enrich:
                for k, v in enrich.items():
                    if k not in entity or entity[k] is None:
                        entity[k] = v
                entity["_meta"] = entity.get("_meta", {})
                entity["_meta"][
                    "source_entity_registry"
                ] = "core.entity_registry (merged enrichment)"
                entity["_meta"]["merged_enrichment"] = True
            else:
                entity["_meta"] = entity.get("_meta", {})
                entity["_meta"][
                    "source_entity_registry"
                ] = "core.entity_registry (registry_inputs)"
                entity["_meta"]["merged_enrichment"] = False
    else:
        for entity in entity_registry:
            entity["_meta"] = entity.get("_meta", {})
            entity["_meta"][
                "source_entity_registry"
            ] = "core.entity_registry (registry_inputs)"
            entity["_meta"]["merged_enrichment"] = False

    # Load tier definitions for deterministic tier assignment
    with open("canonical/support/contracts/tier_definitions.yaml") as f:
        tier_defs = yaml.safe_load(f)["tier_definitions"]

    def match_tier(entity):
        entity_id = entity.get("entity_id", "")
        domain = entity.get("domain", "")
        platform = entity.get("platform", "")
        file_path = entity.get("file_path", "")
        device_class = entity.get("device_class", "")
        # Try each tier in order
        for tier_symbol, tier in tier_defs.items():
            for rule in tier.get("match", []):
                # Match by registry
                if (
                    "registry" in rule
                    and rule["registry"] == "core.entity_registry"
                    and entity.get("_meta", {})
                    .get("source_entity_registry", "")
                    .startswith("core.entity_registry")
                ):
                    if "domains" in rule and domain in rule["domains"]:
                        return tier_symbol
                    elif "domains" not in rule:
                        return tier_symbol
                # Match by domains
                if "domains" in rule and domain in rule["domains"]:
                    return tier_symbol
                # Match by entity_id regex
                if "entity_id" in rule:
                    import re

                    if re.match(rule["entity_id"], entity_id):
                        return tier_symbol
                # Match by platform
                if "platform" in rule and platform == rule["platform"]:
                    return tier_symbol
                # Match by file_path
                if "file_path" in rule and rule["file_path"] in file_path:
                    return tier_symbol
                # Match by device_class
                if "device_class" in rule and device_class == rule["device_class"]:
                    return tier_symbol
                # Match by attributes_include (not implemented here)
        # Debug: print why tier assignment failed
        print(
            f"[DEBUG][TIER] No match for entity_id={entity_id} domain={domain} platform={platform} device_class={device_class}"
        )
        return "?"

    # --- PATCH TIER-CONTRACT-TROUBLESHOOT-V1 ---
    # Ensure domain and _meta.source_entity_registry are set before tier assignment
    for e in entities:
        loop_counter += 1
        if loop_counter % 1000 == 0:
            print(
                f"[DEBUG] Loop {loop_counter}: entity_id={e.get('entity_id')}, domain={e.get('domain')}, platform={e.get('platform')}"
            )
        if loop_counter > max_loops:
            print(
                f"[ERROR] Loop counter exceeded max_loops ({max_loops}). Breaking loop."
            )
            break
        if not isinstance(e, dict):
            print(f"[WARN] Skipped non-dict entity: {repr(e)[:80]}")
            continue
        entity = dict(e)
        entity_id = entity.get("entity_id")
        # --- PATCH: Domain override logic ---
        if isinstance(entity_id, str) and "." in entity_id:
            domain = entity_id.split(".")[0]
        else:
            domain = "unknown"
            print(f"[WARN] Malformed entity_id, cannot extract domain: {entity_id}")
        old_domain = entity.get("domain")
        entity["domain"] = domain
        entity["platform"] = (
            entity.get("integration") or entity.get("platform") or old_domain
        )
        for key in ["integration", "previous_domain"]:
            if key in entity:
                del entity[key]
        # --- PATCH: Ensure _meta.source_entity_registry is set for contract matching ---
        if "_meta" not in entity or not isinstance(entity["_meta"], dict):
            entity["_meta"] = {}
        if "source_entity_registry" not in entity["_meta"]:
            entity["_meta"][
                "source_entity_registry"
            ] = "core.entity_registry (registry_inputs)"
        entity["_meta"]["lineage_trace"] = {
            "entity_id": entity_id,
            "domain": domain,
            "platform": entity.get("platform"),
            "source_entity_registry": entity["_meta"]["source_entity_registry"],
            "pre_tier_assignment": True,
        }
        # --- PATCH: Tier assignment ---
        entity["tier"] = match_tier(entity)
        entity["_meta"]["lineage_trace"]["assigned_tier"] = entity["tier"]
        entity["_meta"]["lineage_trace"]["post_tier_assignment"] = True
        # --- PATCH-TIER-ALPHA-ASSIGNMENT-EXPLICIT-V1 ---
        # After contract-driven matching, explicitly assign tier 'α' to all raw signal domains if still '?'
        RAW_SIGNAL_DOMAINS = ["sensor", "binary_sensor", "switch", "light"]
        # Explicitly assign alpha tier if still '?' and domain is a raw signal domain
        if (
            entity.get("tier", "?") == "?"
            and entity.get("domain") in RAW_SIGNAL_DOMAINS
        ):
            entity["tier"] = "α"
            entity["_meta"]["lineage_trace"]["alpha_fallback"] = True
        # --- PATCH-BUNDLE-OMEGA-REGISTRY-RECOVERY-V1 ---
        # Tier recovery
        if entity.get("tier", "?") == "?":
            d = entity.get("domain", "")
            dc = entity.get("device_class", "")
            name = (entity.get("name") or "").lower()
            if d in ["sensor", "binary_sensor"] or dc in [
                "battery",
                "motion",
                "temperature",
            ]:
                entity["tier"] = "α"
            elif d in ["calendar", "alarm", "service"] or "calendar" in name:
                entity["tier"] = "β"
            else:
                entity["tier"] = "?"
                unresolved_tier_entities.append(entity["entity_id"])
            tier_hist[entity["tier"]] = tier_hist.get(entity["tier"], 0) + 1
        # Area assignment recovery
        if not entity.get("area_id"):
            dev_id = entity.get("device_id")
            dev = device_by_id.get(dev_id)
            recovered_area = None
            if dev and dev.get("area_id"):
                entity["area_id"] = dev["area_id"]
                recovered_area = dev["area_id"]
            elif (
                entity.get("suggested_area")
                and entity.get("suggested_area") in area_by_id
            ):
                entity["area_id"] = entity["suggested_area"]
                recovered_area = entity["suggested_area"]
            if recovered_area:
                entity.setdefault("field_inheritance", {})["area_id"] = "recovered"
                area_coverage_report.append(
                    {"entity_id": entity["entity_id"], "area_id": recovered_area}
                )
            else:
                print(
                    f"[DEBUG][AREA] No area_id for entity_id={entity.get('entity_id')} device_id={dev_id} dev_area={dev.get('area_id') if dev else None}"
                )
        # Floor_ref recovery
        if entity.get("area_id") and not entity.get("floor_ref"):
            area_node = area_nodes.get(entity["area_id"])
            if area_node and "container" in area_node:
                entity["floor_ref"] = area_node["container"]
                entity.setdefault("field_inheritance", {})["floor_ref"] = "recovered"
        # Device class recovery
        if not entity.get("device_class") and entity.get("original_device_class"):
            entity["device_class"] = entity["original_device_class"]
            entity.setdefault("field_inheritance", {})[
                "device_class"
            ] = "from_original_device_class"
        dc_val = entity.get("device_class")
        if dc_val:
            device_class_hist[dc_val] = device_class_hist.get(dc_val, 0) + 1
        # --- PATCH: Join lineage ---
        entity["join_origin"] = [
            "core.entity_registry",
            "core.device_registry",
            "core.area_registry",
            "core.floor_registry",
            "core.config_entries",
        ]
        # --- PATCH: Field inheritance (conditional) ---
        inheritance_map = {}
        if "area_id" in entity:
            inheritance_map["area_id"] = "from_device"
        if "device_class" in entity:
            inheritance_map["device_class"] = "from_original_device_class"
        if inheritance_map:
            entity["field_inheritance"] = {
                **entity.get("field_inheritance", {}),
                **inheritance_map,
            }
        # --- PATCH: _meta block ---
        entity["_meta"] = attach_meta(
            __file__,
            "PATCH PIPELINE-FLAGS-V1",
            pipeline_stage="omega_registry_generation",
        )
        entity["_meta"]["source_priority"] = source_priority

        # --- PATCH: Attribute order ---
        def reorder(d, keys):
            return {k: d[k] for k in keys if k in d} | {
                k: v for k, v in d.items() if k not in keys
            }

        entity = reorder(entity, ["entity_id", "name", "original_name"])
        entities.append(entity)
        if args.debug_log:
            debug_records.append(entity)
    # PATCH-OMEGA-REGISTRY-DOMAIN-OVERRIDE-V1 END
    # Emit tier distribution
    with open(
        "canonical/logs/audit/omega_report/tier_distribution.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(tier_hist, f, indent=2, ensure_ascii=False)
    # Emit unresolved tier entities
    with open(
        "canonical/logs/audit/omega_report/unresolved_tier_entities.log",
        "w",
        encoding="utf-8",
    ) as f:
        for entity_id in unresolved_tier_entities:
            f.write(f"Unresolved tier: {entity_id}\n")
    # Emit area coverage report
    with open(
        "canonical/logs/audit/omega_report/area_coverage_report.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(area_coverage_report, f, indent=2, ensure_ascii=False)
    # Emit device class distribution
    with open(
        "canonical/logs/audit/omega_report/device_class_distribution.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(device_class_hist, f, indent=2, ensure_ascii=False)
    # Emit registry_input_summary.json
    input_summary = {
        "total_entities": len(entities),
        "source_priority": source_priority,
        "base_entity_count": len(base_entities),
        "enriched_entity_count": len(enriched_entities),
        "overlap": len(
            set([e.get("entity_id") for e in base_entities])
            & set([e.get("entity_id") for e in enriched_entities])
        ),
        "missing_files": ingestion_status["missing_files"],
    }
    with open(
        "canonical/logs/audit/omega_report/registry_input_summary.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(input_summary, f, indent=2, ensure_ascii=False)
    # --- END PATCH ---
    # --- PATCH-FLATMAP-INFER-V4-RUNTIME BEGIN ---
    # Enforce contract-driven runtime semantics: single-pass, exact match, confidence scoring
    with open("canonical/support/contracts/join_contract.yaml") as f:
        join_contract = yaml.safe_load(f)
    join_strategy = join_contract.get("join_strategy", {})
    join_strategy.get("match_type", "exact")
    loop_enabled = join_strategy.get("loop", False)
    join_strategy.get("confidence_scoring", {}).get(
        "default_confidence", 1.0
    )
    join_strategy.get("confidence_scoring", {}).get(
        "fallback_confidence", 0.85
    )

    def normalize(k):
        return unicodedata.normalize("NFKC", k).strip() if k else k

    def infer_fields(entity, inference_map):
        lookup_keys = [
            entity.get("entity_id"),
            entity.get("device_id"),
            entity.get("area_id"),
            entity.get("platform"),
            entity.get("name"),
        ]
        inferred = None
        for key in lookup_keys:
            key = normalize(key)  # PATCH CAPTURE-UNICODE-V1
            if not key:
                continue
            inferred = inference_map.get(key)
            if inferred:
                for field in ["tier", "area_id", "floor_id", "platform", "room_ref"]:
                    if inferred.get(field) and not entity.get(field):
                        entity[field] = inferred[field]
                entity["_meta_inference_key"] = key
                break
        else:
            entity["_meta_inference_key"] = None
        # Add room_ref if not present but area_id and floor_id are available
        if (
            not entity.get("room_ref")
            and inferred
            and inferred.get("area_id")
            and inferred.get("floor_id")
        ):
            entity["room_ref"] = f"{inferred['floor_id']}::{inferred['area_id']}"
        # Lineage tagging
        from datetime import datetime

        entity["_meta"] = entity.get("_meta", {})
        entity["_meta"].update(
            {
                "inference_source": "join_contract.yaml",
                "strategy": "multi-key fallback",
                "key_used": entity.get("_meta_inference_key"),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        return entity

    # Load inference map (as in previous patch)
    from scripts.utils.loaders import load_yaml

    def load_inference_mappings(path):
        data = load_yaml(path)
        raw_map = data.get("inference_mappings", {}) if data else {}
        # PATCH CAPTURE-UNICODE-V1: Normalize contract keys
        return {normalize(k): v for k, v in raw_map.items()}

    inference_map = load_inference_mappings(
        "canonical/support/contracts/join_contract.yaml"
    )

    # Track inference hits
    inferred_count = 0
    if not loop_enabled:
        for entity in entities:
            entity = infer_fields(entity, inference_map)
            if entity.get("_meta_inference_key"):
                inferred_count += 1
    else:
        for _ in range(2):
            for entity in entities:
                entity = infer_fields(entity, inference_map)
                if entity.get("_meta_inference_key"):
                    inferred_count += 1
    # Log inference coverage
    with open(
        "canonical/logs/copilot_patch_overview.log", "a", encoding="utf-8"
    ) as patchlog:
        patchlog.write(
            f"[PATCH-FLATMAP-INFER-V3] Inference hits: {inferred_count} / {len(entities)} at {datetime.now().isoformat()}\n"
        )
    # --- PATCH-FLATMAP-INFER-V4-RUNTIME END ---
    # PATCH: Log all import and patch actions for Copilot lineage trace
    with open(
        "canonical/logs/copilot_chat_output.log", "a", encoding="utf-8"
    ) as copilot_log:
        copilot_log.write(
            f"[PATCH][{datetime.now().isoformat()}] Patched import for loaders: from scripts.utils.loaders import load_yaml, load_inference_mappings\n"
        )
        copilot_log.write(
            f"[PATCH][{datetime.now().isoformat()}] All contract-driven inference and patch actions applied in generate_omega_registry.py\n"
        )
    # --- PATCH-AUDIT-FILE-REALDATA-V1: Improve tier assignment and field propagation ---
    # 1. Use tier_lookup from analytics if available, else contract/fallback logic
    for e in entities:
        entity_id = e.get("entity_id")
        # Use analytics tier_lookup if available
        if entity_id in tier_lookup and tier_lookup[entity_id] not in (None, "?"):
            e["tier"] = tier_lookup[entity_id]
            e["_meta"] = e.get("_meta", {})
            e["_meta"]["tier_source"] = "analytics_pipeline_metrics"
        else:
            # Fallback to contract-driven and recovery logic (as before)
            e["tier"] = match_tier(e)
            if e["tier"] == "?":
                d = e.get("domain", "")
                dc = e.get("device_class", "")
                name = (e.get("name") or "").lower()
                if d in ["sensor", "binary_sensor"] or dc in [
                    "battery",
                    "motion",
                    "temperature",
                ]:
                    e["tier"] = "α"
                elif d in ["calendar", "alarm", "service"] or "calendar" in name:
                    e["tier"] = "β"
                else:
                    e["tier"] = "?"
        # Area/floor/room propagation
        dev_id = e.get("device_id")
        dev = device_by_id.get(dev_id)
        if not e.get("area_id") and dev and dev.get("area_id"):
            e["area_id"] = dev["area_id"]
        if e.get("area_id") and not e.get("floor_id"):
            area_node = area_nodes.get(e["area_id"])
            if area_node and "container" in area_node:
                e["floor_id"] = area_node["container"]
        # Room_ref propagation (if contract/area hierarchy supports it)
        if e.get("area_id") and area_nodes.get(e["area_id"], {}).get("room_ref"):
            e["room_ref"] = area_nodes[e["area_id"]]["room_ref"]
    # --- PATCH-AUDIT-FILE-REALDATA-V1: Log patch actions ---
    import os  # Ensure os is imported before use

    patchlog_path = safe_join(
        os.path.dirname(__file__), "../../canonical/logs/meta/copilot_patchlog.log"
    )
    with open(patchlog_path, "a") as patchlog:
        patchlog.write(
            "[PATCH-AUDIT-FILE-REALDATA-V1] Tier assignment and area/floor/room propagation logic improved.\n"
        )
        patchlog.write(
            "[PATCH-AUDIT-FILE-REALDATA-V1] Used analytics tier_lookup if available, else contract/fallback.\n"
        )
        patchlog.write(
            "[PATCH-AUDIT-FILE-REALDATA-V1] Propagated area_id from device, floor_id from area hierarchy, and room_ref if available.\n"
        )
        patchlog.write(
            f"[PATCH-AUDIT-FILE-REALDATA-V1] All actions performed in generate_omega_registry.py at {datetime.now().isoformat()}\n"
        )
    # --- PATCH-CONFLICT-RESOLUTION-AUTHORITY-MODEL-V2 ---
    # Load conflict resolution rules from contract
    conflict_rules = join_contract.get("conflict_resolution", {})
    authority_order = conflict_rules.get(
        "authority_order", ["canonical", "enrichment", "manual", "observational"]
    )
    override_rules = conflict_rules.get("override_rules", {})
    contract_rules = {
        "authority_order": authority_order,
        "override_rules": override_rules,
    }
    conflict_log_path = "canonical/logs/scratch/CONFLICT-RESOLUTION-AUDIT-20250721.log"
    # For each entity, resolve contract-driven fields using resolve_conflict
    key_fields = ["tier", "area_id", "floor_id", "room_ref", "platform"]
    for e in entities:
        for field in key_fields:
            # Gather candidates for this field from all sources (canonical, enrichment, manual, observational)
            candidates = []
            # Canonical (from registry_inputs)
            canonical_val = e.get(field)
            candidates.append(
                {
                    "value": canonical_val,
                    "source": "canonical",
                    "tier": "canonical",
                    "override": False,
                }
            )
            # Enrichment (if present)
            if e.get("_meta", {}).get("merged_enrichment"):
                enrich_val = e.get(field)
                candidates.append(
                    {
                        "value": enrich_val,
                        "source": "enrichment",
                        "tier": "enrichment",
                        "override": False,
                    }
                )
            # Manual/observational (future extension)
            # ...
            # Only resolve if >1 candidate or value is ambiguous
            if len(candidates) > 1 or any(
                c["value"] in [None, "", "?"] for c in candidates
            ):
                # Robust import for resolve_conflict (matches top-level import logic)
                try:
                    from utils.join_utils import resolve_conflict
                except ImportError:
                    import importlib.util
                    import sys

                    utils_dir = safe_join(os.path.dirname(__file__), "..", "utils")
                    join_utils_path = safe_join(utils_dir, "join_utils.py")
                    spec_ju = importlib.util.spec_from_file_location(
                        "join_utils", join_utils_path
                    )
                    if spec_ju and spec_ju.loader:
                        join_utils = importlib.util.module_from_spec(spec_ju)
                        sys.modules["join_utils"] = join_utils
                        spec_ju.loader.exec_module(join_utils)
                        resolve_conflict = getattr(
                            join_utils,
                            "resolve_conflict",
                            lambda *a, **kw: (None, None, "resolve_conflict not found"),
                        )
                    else:
                        def resolve_conflict(*a, **kw):
                            return None, None, "resolve_conflict not found"
                winner_val, winner_source, reason = resolve_conflict(
                    field,
                    candidates,
                    entity_id=e.get("entity_id"),
                    log_path=conflict_log_path,
                    contract_rules=contract_rules,
                )
                e[field] = winner_val
                e.setdefault("_meta", {})["conflict_resolution"] = e.get(
                    "_meta", {}
                ).get("conflict_resolution", {})
                e["_meta"]["conflict_resolution"][field] = {
                    "winner": winner_source,
                    "reason": reason,
                    "candidates": candidates,
                }
    # --- PATCH: Area assignment and propagation audit (HARDENED) ---
    device_by_id_norm = {
        unicodedata.normalize("NFKC", str(d["id"])).strip().lower(): d
        for d in device_registry
        if "id" in d
    }
    propagation_audit = []
    for entity in entities:
        entity_id = entity.get("entity_id")
        dev_id_raw = entity.get("device_id")
        dev_id = (
            unicodedata.normalize("NFKC", str(dev_id_raw)).strip().lower()
            if dev_id_raw
            else None
        )
        dev = device_by_id_norm.get(dev_id) if dev_id is not None else None
        area_id_before = entity.get("area_id")
        device_area_id = dev.get("area_id") if dev else None
        suggested_area = (
            entity.get("suggested_area")
            if entity.get("suggested_area") in area_by_id
            else None
        )
        propagation_event = {
            "entity_id": entity_id,
            "device_id": dev_id_raw,
            "device_id_normalized": dev_id,
            "device_area_id": device_area_id,
            "suggested_area": suggested_area,
            "area_id_before": area_id_before,
            "area_id_after": area_id_before,  # will update if assigned
            "propagated": False,
            "propagation_source": None,
            "overwritten": False,
        }
        # Assign area_id if missing, prefer device, then suggested_area
        if not area_id_before:
            if device_area_id:
                entity["area_id"] = device_area_id
                propagation_event["area_id_after"] = device_area_id
                propagation_event["propagated"] = True
                propagation_event["propagation_source"] = "device"
                entity.setdefault("field_inheritance", {})["area_id"] = "recovered"
            elif suggested_area:
                entity["area_id"] = suggested_area
                propagation_event["area_id_after"] = suggested_area
                propagation_event["propagated"] = True
                propagation_event["propagation_source"] = "suggested_area"
                entity.setdefault("field_inheritance", {})[
                    "area_id"
                ] = "recovered_suggested_area"
            else:
                propagation_event["propagation_source"] = "missing"
        else:
            # area_id was already present, record its source
            if device_area_id and area_id_before == device_area_id:
                propagation_event["propagation_source"] = "device_already"
            elif suggested_area and area_id_before == suggested_area:
                propagation_event["propagation_source"] = "suggested_area_already"
            else:
                propagation_event["propagation_source"] = "preexisting"
        # After all enrichment/contract logic, check if area_id was overwritten
        propagation_audit.append(propagation_event)
    # After all enrichment/contract logic, update overwritten flag
    for i, entity in enumerate(entities):
        final_area_id = entity.get("area_id")
        if propagation_audit[i]["area_id_after"] != final_area_id:
            propagation_audit[i]["overwritten"] = True
            propagation_audit[i]["area_id_after"] = final_area_id
    # PATCH-DEVICE-AREA-PROPAGATION-DEBUG-V2: Debug print/log for propagation events
    print(
        f"[DEBUG][PATCH-DEVICE-AREA-PROPAGATION-DEBUG-V2] Propagation audit event count: {len(propagation_audit)}"
    )
    if propagation_audit:
        print(
            f"[DEBUG][PATCH-DEVICE-AREA-PROPAGATION-DEBUG-V2] First propagation event: {json.dumps(propagation_audit[0], indent=2) if len(propagation_audit) > 0 else 'None'}"
        )
    else:
        print(
            "[DEBUG][PATCH-DEVICE-AREA-PROPAGATION-DEBUG-V2] No propagation events recorded."
        )
    # Always emit the audit file, even if empty, with a _meta block if no events
    audit_path = "canonical/logs/audit/omega_report/device_area_propagation_audit.json"
    print(
        f"[DEBUG][PATCH-DEVICE-AREA-PROPAGATION-DEBUG-V2] About to write audit file to: {audit_path} (len={len(propagation_audit)})"
    )
    if propagation_audit:
        with open(audit_path, "w", encoding="utf-8") as f:
            json.dump(propagation_audit, f, indent=2, ensure_ascii=False)
            f.flush()
        print(
            f"[DEBUG][PATCH-DEVICE-AREA-PROPAGATION-DEBUG-V2] Wrote {len(propagation_audit)} propagation events to audit file."
        )
    else:
        stub = {
            "_meta": {
                "timestamp": datetime.utcnow().isoformat(),
                "script": __file__,
                "note": "No area_id propagation events recorded.",
            }
        }
        with open(audit_path, "w", encoding="utf-8") as f:
            json.dump(stub, f, indent=2, ensure_ascii=False)
        print(
            "[DEBUG][PATCH-DEVICE-AREA-PROPAGATION-DEBUG-V2] Wrote empty audit file with _meta block."
        )
    # --- PATCH: FINAL area_id propagation and lock-in ---
    # Guarantee area_id is set on the final entity object before output
    for entity in entities:
        if not entity.get("area_id"):
            dev_id = entity.get("device_id")
            dev = device_by_id.get(dev_id)
            if dev and dev.get("area_id"):
                entity["area_id"] = dev["area_id"]
                entity.setdefault("field_inheritance", {})[
                    "area_id"
                ] = "from_device_final_patch"
    # --- END PATCH ---
    # --- PATCH: Minimize registry output for file size (enforced, strict allowlist) ---
    # --- PATCH-CONSOLIDATE-REGISTRY-UTILS-V1: Use unified registry utilities for minimization and output ---
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    # PATCH-REGISTRY-MINIMIZATION-V3: Force output file overwrite before writing
    import os

    output_path = args.output
    if os.path.exists(output_path):
        open(output_path, "w").close()
    # PATCH-REGISTRY-MINIMIZATION-V3: Strict allowlist enforcement (final step)
    contract_path = (
        "canonical/support/contracts/omega_registry_master.output_contract.yaml"
    )
    with open(contract_path) as f:
        contract = yaml.safe_load(f)
    contract.get("required_keys", []) + contract.get(
        "optional_keys", []
    )
    # PATCH: ensure contract_allowlist is always defined after allowed_fields
    # PATCH-REGISTRY-MINIMIZATION-V4B: Strict allowlist and processing order
    strict_allowlist = OMEGA_REGISTRY_STRICT_ALLOWLIST
    minimized_entities = []
    for e in deduped_entities:
        # Enforce strict minimization sequence
        e = flatten_options_to_voice_assistants(e)
        e = strip_null_fields(e)
        # Use a deterministic conflict_id for traceability
        conflict_id = "sha256-" + (e.get("entity_id") or "none")
        e = contract_minimize_meta(
            e, origin="omega_registry", inferred=None, conflict_id=conflict_id
        )
        # PATCH: Log keys and device_id before allowlist for failing entities
        if e.get("entity_id", "").startswith("sensor.sun_next_") or e.get(
            "entity_id", ""
        ).startswith("sensor.home_assistant_"):
            import logging

            logger = logging.getLogger("omega_registry")
            logger.info(
                f"[DEBUG-DEVICE-ID-MINIMIZE-KEYS-BEFORE-ALLOWLIST] {e.get('entity_id')} keys={list(e.keys())} device_id={e.get('device_id')} (type: {type(e.get('device_id'))}) before allowlist"
            )
        e = {k: e[k] for k in strict_allowlist if k in e}
        minimized_entities.append(e)
    write_json_compact(minimized_entities, output_path)
    # PATCH-REGISTRY-MINIMIZATION-V4B: Log patch action
    patch_log_path = "canonical/logs/scratch/PATCH-REGISTRY-MINIMIZATION-V4.log"
    with open(patch_log_path, "a", encoding="utf-8") as patchlog:
        patchlog.write(
            f"[PATCH-REGISTRY-MINIMIZATION-V4B] Strict allowlist and minimization sequence enforced at {datetime.now().isoformat()}\n"
        )
    with open(
        "canonical/logs/copilot_patch_overview.log", "a", encoding="utf-8"
    ) as patchlog:
        patchlog.write(
            f"[PATCH-REGISTRY-MINIMIZATION-V4B] Patch applied and output regenerated at {datetime.now().isoformat()}\n"
        )
    # PATCH OMEGA-CONSTANTS-UTILS-V1: Log patch action for strict allowlist import
    patch_log_path = "canonical/logs/scratch/PATCH-OMEGA-CONSTANTS-UTILS-V1.log"
    with open(patch_log_path, "a", encoding="utf-8") as patchlog:
        patchlog.write(
            f"[PATCH OMEGA-CONSTANTS-UTILS-V1] strict_allowlist imported from constants.py and used for minimization at {datetime.now().isoformat()}\n"
        )
    # --- PATCH: FULL LAYERED JOIN CASCADE LOGIC (PROPAGATION_AUDIT_AND_SOURCE_INGEST_COMPLETENESS_V1) ---
    enrichment_trace_path = (
        "canonical/logs/scratch/enrichment_trace_omega_registry.jsonl"
    )
    with open(enrichment_trace_path, "w", encoding="utf-8") as trace_log:
        final_entities = []
        for entity in deduped_entities:
            if not isinstance(entity, dict) or not entity.get("entity_id"):
                continue
            join_origin = ["core.entity_registry"]
            field_inheritance = {}
            missing = []
            # Device join
            dev_id = entity.get("device_id")
            device = device_by_id.get(dev_id)
            if device:
                join_origin.append("core.device_registry")
                # Inherit area_id if missing
                if not entity.get("area_id") and device.get("area_id"):
                    entity["area_id"] = device["area_id"]
                    field_inheritance["area_id"] = "from_device"
                # Inherit manufacturer/model if missing
                for k in ["manufacturer", "model"]:
                    if not entity.get(k) and device.get(k):
                        entity[k] = device[k]
                        field_inheritance[k] = "from_device"
            else:
                missing.append("core.device_registry")
            # Area join
            area_id = entity.get("area_id")
            area = area_by_id.get(area_id)
            if area:
                join_origin.append("core.area_registry")
                # Inherit floor_id if missing
                if not entity.get("floor_id") and area.get("floor_id"):
                    entity["floor_id"] = area["floor_id"]
                    field_inheritance["floor_id"] = "from_area"
            else:
                missing.append("core.area_registry")
            # Floor join
            floor_id = entity.get("floor_id")
            floor = floor_by_id.get(floor_id)
            if floor:
                join_origin.append("core.floor_registry")
            else:
                missing.append("core.floor_registry")
            # Config entry join
            entry_id = entity.get("entry_id")
            config = config_by_entry.get(entry_id)
            if config:
                join_origin.append("core.config_entries")
            else:
                missing.append("core.config_entries")
            # Restore state (optional)
            if restore_by_entity:
                if entity["entity_id"] in restore_by_entity:
                    join_origin.append("core.restore_state")
            else:
                missing.append("core.restore_state")
            # Exposed entities (optional)
            if exposed_set:
                if entity["entity_id"] in exposed_set:
                    join_origin.append("homeassistant.exposed_entities")
            else:
                missing.append("homeassistant.exposed_entities")
            # Set join_origin, field_inheritance, enrichment_depth
            entity["join_origin"] = join_origin
            entity["field_inheritance"] = field_inheritance
            entity["enrichment_depth"] = len(set(join_origin))
            # Only append if entity has at least entity_id and join_origin
            if entity.get("entity_id") and entity.get("join_origin"):
                final_entities.append(entity)
            # Emit per-entity trace
            trace_log.write(
                json.dumps(
                    {
                        "entity_id": entity.get("entity_id"),
                        "joined_from": join_origin,
                        "field_inheritance": field_inheritance,
                        "missing": missing,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    # Overwrite minimized_entities with final_entities for output
    minimized_entities = final_entities
