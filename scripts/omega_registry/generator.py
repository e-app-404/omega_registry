"""
PATCH-OMEGA-REGISTRY-REFACTOR-V1: Main generator orchestration for omega registry.
Coordinates loading, minimization, contract parsing, and writing.
PATCH-OMEGA-PIPELINE-DEBUG-LOGGING-V1: Deferred minimization, soft allowlist logging, null retention, contract validation, and centralized logging.
"""

import argparse
import json
import logging
import os
from datetime import datetime
from pathlib import Path

import yaml

from scripts.enrich.enrich_orchestrator import run_enrichment_pipeline
from scripts.enrich.normalize import normalize_entity_fields
from scripts.omega_registry.contract import (
    expand_contract_if_missing,
    get_allowlist,
    get_required_keys,
)
from scripts.omega_registry.loaders import load_json_with_extract
from scripts.omega_registry.minimizer import (
    contract_minimize_meta,
    enforce_allowlist,
    flatten_options_to_voice_assistants,
    strip_null_fields,
)
from scripts.omega_registry.utils import generate_conflict_id
from scripts.omega_registry.writer import deduplicate_entities, write_registry
from scripts.utils import pipeline_config as cfg
from scripts.utils.logging import setup_logging

setup_logging(cfg.LOGS_DIR / "omega_registry_generator.log")
logger = logging.getLogger("omega_registry")


def parse_args():
    parser = argparse.ArgumentParser(description="Omega Registry Generator")
    parser.add_argument(
        "--output-profile",
        type=str,
        default=None,
        help="Output profile: slim, default, audit",
    )
    parser.add_argument(
        "--emit-alpha",
        action="store_true",
        default=False,
        help="Emit per-domain alpha registries via writer (dry-run by default)",
    )
    parser.add_argument(
        "--emit-alpha-write",
        action="store_true",
        default=False,
        help="When used with --emit-alpha, actually write alpha registry files to disk",
    )
    parser.add_argument(
        "--alpha-mode",
        choices=["off", "dry", "write"],
        default="off",
        help=(
            "Alpha emission mode: 'off' (no alpha outputs), 'dry' (emit but do not write), "
            "or 'write' (emit and write alpha registries). Legacy flags --emit-alpha/--emit-alpha-write "
            "are still accepted and will take precedence if provided."
        ),
    )
    # ... add other args as needed ...
    return parser.parse_args()


def generate(
    output_path,
    contract_path,
    input_paths,
    strict=False,
    profile=None,
    emit_alpha: bool = False,
    emit_alpha_write: bool = False,
):
    print("[INFO] Starting registry generation sequence")
    # Load all input entities
    print("[INFO] Loading registry inputs...")
    entities = []
    loaded_files = []
    missing_files = []
    for path in input_paths:
        if os.path.exists(path):
            loaded_files.append(path)
            entities.extend(load_json_with_extract(path))
        else:
            missing_files.append(path)
    logger.info(
        f"[PATCH-OMEGA-PIPELINE-DEBUG-LOGGING-V1] Registry input summary: loaded={len(loaded_files)}, missing={len(missing_files)}"
    )
    if missing_files:
        logger.warning(f"Missing input files: {missing_files}")
    # Deduplicate
    entities = deduplicate_entities(entities)
    logger.info(f"Deduplicated entity count: {len(entities)}")
    # --- PATCH: Log device_id presence for all entities before writing merged file ---
    device_id_stats = {"present": 0, "missing": 0, "null": 0}
    for e in entities:
        if "device_id" not in e:
            device_id_stats["missing"] += 1
        elif e["device_id"] is None:
            device_id_stats["null"] += 1
        else:
            device_id_stats["present"] += 1
    logger.info(
        f"[DEBUG-DEVICE-ID] device_id stats before enrichment input: present={device_id_stats['present']} null={device_id_stats['null']} missing={device_id_stats['missing']} total={len(entities)}"
    )
    # Validate contract required_keys
    print("[INFO] Validating contract...")
    required_keys = get_required_keys(contract_path)
    expected_keys = ["entity_id", "platform", "area_id", "tier"]
    missing_keys = [k for k in expected_keys if k not in required_keys]
    if missing_keys:
        logger.warning(
            f"Contract missing required keys: {missing_keys}. Expanding contract."
        )
        expand_contract_if_missing(contract_path, missing_keys)
        required_keys = get_required_keys(contract_path)
    logger.info(f"Contract required_keys: {required_keys}")
    print("[INFO] Invoking enrichment phase...")
    # Write the merged entities to a temp file for enrichment input
    temp_input_path = "canonical/derived_views/merged_entity_registry.json"
    Path(temp_input_path).parent.mkdir(parents=True, exist_ok=True)
    with open(temp_input_path, "w", encoding="utf-8") as f:
        json.dump(entities, f, indent=2)
    logger.info(
        f"[DEBUG-MERGED-ENTITY-REGISTRY] Wrote merged entity registry to {temp_input_path} with {len(entities)} entities."
    )

    # --- NEW: Use orchestrator and normalization directly ---
    from scripts.utils.input_list_extract import extract_data

    # Load lookups and join_chains as in the old engine
    def load_json_file(path):
        with open(path, "r") as f:
            return json.load(f)

    def load_yaml_file(path):
        with open(path, "r") as f:
            return yaml.safe_load(f)

    lookups = {}
    if os.path.exists(str(cfg.DEVICE_REGISTRY)):
        lookups["device_registry"] = extract_data(
            str(cfg.DEVICE_REGISTRY), load_json_file(str(cfg.DEVICE_REGISTRY))
        )
    if os.path.exists(str(cfg.AREA_REGISTRY)):
        lookups["area_registry"] = extract_data(
            str(cfg.AREA_REGISTRY), load_json_file(str(cfg.AREA_REGISTRY))
        )
    if os.path.exists(str(cfg.FLOOR_REGISTRY)):
        lookups["floor_registry"] = extract_data(
            str(cfg.FLOOR_REGISTRY), load_json_file(str(cfg.FLOOR_REGISTRY))
        )
    if os.path.exists(str(cfg.INTEGRATION_REGISTRY)):
        lookups["config_registry"] = extract_data(
            str(cfg.INTEGRATION_REGISTRY),
            load_json_file(str(cfg.INTEGRATION_REGISTRY)),
        )
    join_chains = {}
    if os.path.exists(str(cfg.JOIN_CONTRACT)):
        join_chains = load_yaml_file(str(cfg.JOIN_CONTRACT))
    context = {
        "device_registry": lookups.get("device_registry", {}),
        "area_registry": lookups.get(
            "area_registry", {}
        ),  # PATCH: ensure area_registry is always present
        "config_registry": lookups.get("config_registry", {}),
        "lookups": lookups,
        "join_chains": join_chains,
        "join_stats": {},
        "join_blocked": {},
    }
    # Log loaded area_registry keys for debugging
    logger.info(
        f"[DEBUG] Loaded area_registry keys: {list(context['area_registry'].keys()) if isinstance(context['area_registry'], dict) else 'not a dict'}"
    )
    hydrated_entities = []
    for entity in entities:
        enriched = run_enrichment_pipeline(entity, context)
        enriched = normalize_entity_fields(enriched)
        hydrated_entities.append(enriched)
    hydration_count = len(hydrated_entities)
    logger.info(
        f"Entity hydration (enrichment) complete. Hydrated count: {hydration_count}"
    )
    print("[INFO] Minimizing and validating entities...")
    # Log entity fields before minimization
    for idx, e in enumerate(hydrated_entities):
        logger.info(f"Entity {idx} pre-minimization fields: {list(e.keys())}")
    # Minimization step (deferred)
    allowlist = get_allowlist(contract_path)
    logger.info(f"[DEBUG-ALLOWLIST] allowlist={allowlist}")
    minimized = []
    for idx, e in enumerate(hydrated_entities):
        e = flatten_options_to_voice_assistants(e)
        # Retain nulls for required_keys
        e = strip_null_fields(e, retain_keys=required_keys)
        entity_id = None
        if isinstance(e, dict):
            entity_id = e.get("entity_id")
        elif isinstance(e, list) and len(e) > 0 and isinstance(e[0], dict):
            entity_id = e[0].get("entity_id")
        conflict_id = generate_conflict_id(entity_id)
        # --- PATCH: Log device_id before minimization ---
        if isinstance(e, dict):
            logger.info(
                f"[DEBUG-DEVICE-ID-MINIMIZE-BEFORE] {entity_id} device_id={e.get('device_id')} (type: {type(e.get('device_id'))}) before minimization"
            )
        if isinstance(e, dict):
            e = contract_minimize_meta(
                e,
                origin="omega_registry",
                inferred=None,
                conflict_id=conflict_id,
            )
            logger.info(
                f"[DEBUG-DEVICE-ID-MINIMIZE-AFTER-META] {entity_id} device_id={e.get('device_id')} (type: {type(e.get('device_id'))}) after contract_minimize_meta"
            )
            pre_fields = set(e.keys())
        else:
            pre_fields = set()
        # PATCH: Log all keys and device_id for failing entities before allowlist
        if isinstance(e, dict):
            eid = e.get("entity_id")
            if isinstance(eid, str) and (
                eid.startswith("sensor.sun_next_")
                or eid.startswith("sensor.home_assistant_")
            ):
                logger.info(
                    f"[DEBUG-DEVICE-ID-MINIMIZE-KEYS-BEFORE-ALLOWLIST] {eid} keys={list(e.keys())} device_id={e.get('device_id')} (type: {type(e.get('device_id'))}) before allowlist"
                )
        if isinstance(e, dict):
            e = enforce_allowlist(e, allowlist)
            logger.info(
                f"[DEBUG-DEVICE-ID-MINIMIZE-AFTER-ALLOWLIST] {entity_id} device_id={e.get('device_id')} (type: {type(e.get('device_id'))}) after enforce_allowlist"
            )
            post_fields = set(e.keys())
            removed_fields = list(pre_fields - post_fields)
            logger.info(
                f"Entity {idx} minimization: retained={list(post_fields)}, removed={removed_fields}"
            )
            minimized.append(e)
        elif isinstance(e, list):
            # If e is a list, apply enforce_allowlist to each dict item
            processed_list = []
            for item in e:
                if isinstance(item, dict):
                    item = enforce_allowlist(item, allowlist)
                processed_list.append(item)
            logger.info(f"Entity {idx} minimization: retained=list, removed=[]")
            minimized.append(processed_list)
        else:
            logger.warning(f"Entity {idx} is of unexpected type: {type(e)}")
            minimized.append(e)
    logger.info(f"Minimization complete. Output entity count: {len(minimized)}")
    # Log device_id after minimization
    for idx, e in enumerate(minimized):
        if isinstance(e, dict):
            logger.info(
                f"[DEBUG-DEVICE-ID-MINIMIZE-AFTER] {e.get('entity_id')} device_id={e.get('device_id')} (type: {type(e.get('device_id'))}) after minimization"
            )
        logger.info(f"Entity {idx} post-minimization fields: {list(e.keys())}")
    # Field integrity validation
    print("[INFO] Writing output to file...")
    from scripts.omega_registry.contract import validate_entity_fields

    validate_entity_fields(minimized, strict=strict)
    # Output profile selection logic
    profile_yaml_path = Path(
        "canonical/support/contracts/registry_output_profiles.yaml"
    )
    with open(profile_yaml_path, "r") as f:
        profiles = yaml.safe_load(f)["output_profiles"]
    if not profile:
        profile = "default"
    if profile not in profiles:
        logger.warning(
            f"Unknown output profile '{profile}', falling back to 'default'."
        )
        profile = "default"
    profile_spec = profiles[profile]
    logger.info(f"[PROFILE] Using output profile: {profile}")
    logger.info(f"[PROFILE] Profile allowlist: {profile_spec.get('allowlist')}")
    # Write output
    write_registry(
        minimized,
        output_path,
        profile=profile,
        profile_yaml_path=profile_yaml_path,
    )
    logger.info(
        f"Registry output written to {output_path} at {datetime.utcnow().isoformat()}Z"
    )
    # Write audit output only if audit mode
    if profile == "audit":
        from scripts.omega_registry.audit_writer import write_audit_registry

        audit_output_path = str(output_path).replace(".json", ".audit.json")
        write_audit_registry(hydrated_entities, audit_output_path)
        logger.info(
            f"Audit registry output written to {audit_output_path} at {datetime.utcnow().isoformat()}Z"
        )
    # Write pretty-printed output
    pretty_output_path = str(output_path).replace(".json", ".pretty.json")
    with open(pretty_output_path, "w", encoding="utf-8") as f:
        json.dump(minimized, f, indent=2, ensure_ascii=False)
    logger.info(
        f"Pretty-printed registry output written to {pretty_output_path}"
    )
    # Write hydrated_entities to canonical/derived_views/hydrated_entities.json (minified and pretty)
    hydrated_dir = Path("canonical/derived_views")
    hydrated_dir.mkdir(parents=True, exist_ok=True)
    hydrated_path = hydrated_dir / "hydrated_entities.json"
    hydrated_pretty_path = hydrated_dir / "hydrated_entities.pretty.json"
    # Write minified
    with open(hydrated_path, "w", encoding="utf-8") as f:
        json.dump(
            hydrated_entities, f, separators=(",", ":"), ensure_ascii=False
        )
    # Write pretty
    with open(hydrated_pretty_path, "w", encoding="utf-8") as f:
        json.dump(hydrated_entities, f, indent=2, ensure_ascii=False)
    logger.info(
        f"Hydrated entities written to {hydrated_path} and {hydrated_pretty_path}"
    )

    # Determine emit_alpha_flag and emit_alpha_write from passed flags and central config
    emit_alpha_flag = bool(getattr(cfg, "EMIT_ALPHA_REGISTRIES", False))
    # Respect explicit call-time flag first (function params), then central config
    if emit_alpha:
        emit_alpha_flag = True

    extra_outputs = []
    if emit_alpha_flag:
        try:
            from scripts.generators.alpha_registry_writer import (
                make_validator_from_contract_module,
                write_alpha_registry,
            )

            validator = make_validator_from_contract_module()

            # Adapter to match writer's loosely-typed expected signature
            def validator_adapter(items_any, contract_path_any=None):
                try:
                    return validator(items_any, contract_path_any)
                except Exception:
                    return ["validator-exception"]

            # Example: emit sensors alpha registry; writes are dry-run unless caller asked otherwise via env
            alpha_sensor_out = str(
                Path("canonical/derived_views") / "alpha_sensor_registry.json"
            )
            sensor_res = write_alpha_registry(
                "alpha_sensors",
                minimized,
                alpha_sensor_out,
                contract_path=None,
                validate_contract=validator_adapter,
                write_output=emit_alpha_write,
                strict=False,
            )
            # If the writer produced a file, include its manifest entry
            if sensor_res.get("written"):
                eo = {
                    "path": str(Path(alpha_sensor_out).absolute()),
                    "sha256": sensor_res.get("sha256"),
                    "phase": "generator:alpha_sensor_writer",
                }
                if sensor_res.get("compliance_report"):
                    eo["compliance_report"] = sensor_res.get(
                        "compliance_report"
                    )
                extra_outputs.append(eo)
            # Example: emit rooms alpha registry from area/floor lookups (best-effort)
            alpha_room_out = str(
                Path("canonical/derived_views") / "alpha_room_registry.json"
            )
            room_items = []
            # Build simple room items from area_registry if available in context
            try:
                area_items = (
                    list(context.get("area_registry", {}).values())
                    if isinstance(context.get("area_registry", {}), dict)
                    else context.get("area_registry", [])
                )
                room_items = area_items
            except Exception:
                room_items = []
            room_res = write_alpha_registry(
                "alpha_rooms",
                room_items,
                alpha_room_out,
                contract_path=None,
                validate_contract=validator_adapter,
                write_output=emit_alpha_write,
                strict=False,
            )
            if room_res.get("written"):
                eo = {
                    "path": str(Path(alpha_room_out).absolute()),
                    "sha256": room_res.get("sha256"),
                    "phase": "generator:alpha_room_writer",
                }
                if room_res.get("compliance_report"):
                    eo["compliance_report"] = room_res.get("compliance_report")
                extra_outputs.append(eo)
        except Exception as exc:
            logger.warning(f"Failed to emit alpha registries: {exc}")

    # Return extra outputs for caller to include in provenance
    return {"extra_outputs": extra_outputs}


if __name__ == "__main__":
    args = parse_args()
    # TODO: Add manifest/config override logic if needed
    result = generate(
        output_path=str(cfg.OUTPUTS_DIR / "omega_registry_master.json"),
        contract_path=str(cfg.OUTPUT_CONTRACT),
        input_paths=[
            str(cfg.INPUTS_DIR / f) for f in os.listdir(cfg.INPUTS_DIR)
        ],
        strict=False,
        profile=args.output_profile or "default",
        emit_alpha=args.emit_alpha,
        emit_alpha_write=args.emit_alpha_write,
    )
    # If the generator returned extra outputs, print them (caller will read updated provenance later)
    if isinstance(result, dict) and result.get("extra_outputs"):
        for eo in result["extra_outputs"]:
            logger.info(
                f"[ALPHA-OUTPUT] {eo.get('path')} sha256={eo.get('sha256')} phase={eo.get('phase')}"
            )
