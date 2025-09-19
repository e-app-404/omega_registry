import logging
import os

import yaml

from scripts.enrich.enrichers.area_floor_enricher import AreaFloorEnricher
from scripts.enrich.enrichers.config_entry_enricher import ConfigEntryEnricher
from scripts.enrich.enrichers.device_enricher import DeviceRegistryEnricher
from scripts.enrich.enrichers.join_enricher import JoinFieldEnricher
from scripts.enrich.enrichers.mobile_app_enricher import MobileAppEnricher
from scripts.enrich.enrichers.name_enricher import NameEnricher
from scripts.enrich.enrichers.network_tracker_enricher import NetworkTrackerEnricher
from scripts.enrich.label_enricher import enrich_labels
from scripts.transformation.tiers import tier_classification
from scripts.utils import pipeline_config as cfg


def load_tier_definitions():
    # Always resolve from workspace root (two levels up from this file)
    workspace_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    TIER_DEFINITIONS_PATH = os.path.join(
        workspace_root,
        "canonical",
        "support",
        "contracts",
        "tier_definitions.yaml",
    )
    with open(TIER_DEFINITIONS_PATH, "r") as f:
        yml = yaml.safe_load(f)
    return yml["tier_definitions"]


def run_enrichment_pipeline(entity, context, gap_log=None, summary=None):
    """
    Orchestrate enrichment by applying all enrichers in sequence.
    Tracks enrichment_depth and _meta.enrichment_depth_trace.
    Logs enrichment gaps and updates summary stats if provided.
    Args:
        entity (dict): The entity to enrich.
        context (dict): Context including lookups, registries, join_chains, etc.
    Returns:
        dict: The fully enriched entity.
    """
    # Instantiate enrichers
    device_enricher = DeviceRegistryEnricher()
    # respect global and per-enricher flags for synthetic device creation
    network_tracker_enricher = NetworkTrackerEnricher(
        create_synthetic=(
            cfg.ENABLE_SYNTHETIC_DEVICE_CREATION or cfg.SYNTHETIC_NETWORK_TRACKER
        )
    )
    config_enricher = ConfigEntryEnricher()
    mobile_app_enricher = MobileAppEnricher(
        create_synthetic=(
            cfg.ENABLE_SYNTHETIC_DEVICE_CREATION or cfg.SYNTHETIC_MOBILE_APP
        )
    )
    join_enricher = JoinFieldEnricher(context.get("join_chains", {}))
    area_floor_enricher = AreaFloorEnricher()
    name_enricher = NameEnricher()

    # --- Label Attribution Heuristic ---
    enriched = enrich_labels(entity)

    # Track enrichment depth
    enriched["enrichment_depth"] = 0
    enriched.setdefault("_meta", {})
    enriched["_meta"].setdefault("enrichment_depth_trace", [])

    def apply_enricher(enricher, name):
        before = enriched.copy()
        result = enricher.enrich(enriched, context)
        if result != before:
            enriched["enrichment_depth"] += 1
            enriched["_meta"]["enrichment_depth_trace"].append(name)
        return result

    # Enrichment order: device → network_tracker → config → mobile_app → join → area/floor → name
    enriched = apply_enricher(device_enricher, "device_enricher")
    enriched = apply_enricher(network_tracker_enricher, "network_tracker_enricher")
    enriched = apply_enricher(config_enricher, "config_entry_enricher")
    enriched = apply_enricher(mobile_app_enricher, "mobile_app_enricher")
    enriched = apply_enricher(join_enricher, "join_enricher")
    enriched = apply_enricher(area_floor_enricher, "area_floor_enricher")
    enriched = apply_enricher(name_enricher, "name_enricher")

    # --- Tier inference ---
    if "tier_definitions" not in context or not context["tier_definitions"]:
        context["tier_definitions"] = load_tier_definitions()
    tier_definitions = context["tier_definitions"]
    tier, origin = tier_classification(
        enriched, tier_definitions, fallback_tier="unclassified"
    )
    if tier:
        enriched["tier"] = tier
        enriched.setdefault("_meta", {}).setdefault("inferred_fields", {})["tier"] = {
            "join_origin": "tier_enricher",
            "join_confidence": 0.9,
            "field_contract": f"tier inferred via {origin}",
        }
    # --- Logging & Alerting for Enrichment Gaps ---
    missing = []
    if not enriched.get("tier"):
        missing.append("tier")
    join_origin = (
        enriched.get("_meta", {})
        .get("inferred_fields", {})
        .get("tier", {})
        .get("join_origin")
    )
    if not join_origin:
        missing.append("join_origin")
    if "enrichment_depth" not in enriched:
        missing.append("enrichment_depth")
    if missing:
        log_msg = {
            "entity_id": enriched.get("entity_id"),
            "missing": missing,
            "enrichment_depth": enriched.get("enrichment_depth"),
            "_meta": enriched.get("_meta", {}),
        }
        if gap_log is not None:
            gap_log.append(log_msg)
        else:
            logging.warning(f"[ENRICHMENT GAP] {log_msg}")
    # --- Summary report update ---
    if summary is not None:
        for field in ("tier", "enrichment_depth"):
            summary.setdefault(field, {"present": 0, "missing": 0})
            if enriched.get(field) is not None:
                summary[field]["present"] += 1
            else:
                summary[field]["missing"] += 1
        # join_origin
        summary.setdefault("join_origin", {"present": 0, "missing": 0})
        if join_origin:
            summary["join_origin"]["present"] += 1
        else:
            summary["join_origin"]["missing"] += 1
    return enriched
