"""
Tier Enricher: Assigns canonical tier to entities using centralized rules.
- Loads tier_definitions.yaml from canonical/support/contracts/
- Uses tier_classification from transformation/tiers.py
- Emits tier at root and in _meta.inferred_fields with provenance
"""

import os

import yaml

from scripts.transformation.tiers import tier_classification

TIER_DEFINITIONS_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    ),
    "canonical",
    "support",
    "contracts",
    "tier_definitions.yaml",
)


def load_tier_definitions():
    with open(TIER_DEFINITIONS_PATH, "r") as f:
        yml = yaml.safe_load(f)
    return yml["tier_definitions"]


def enrich_entity_with_tier(entity, tier_definitions=None):
    if tier_definitions is None:
        tier_definitions = load_tier_definitions()
    # Extract tier from unique_id/entity_id if present
    tier = None
    match_origin = None
    if "unique_id" in entity and entity["unique_id"]:
        # Example: parse tier from unique_id if encoded
        if "alpha" in entity["unique_id"]:
            tier = "α"
            match_origin = "unique_id"
        elif "beta" in entity["unique_id"]:
            tier = "β"
            match_origin = "unique_id"
        elif "gamma" in entity["unique_id"]:
            tier = "γ"
            match_origin = "unique_id"
    if not tier and "entity_id" in entity and entity["entity_id"]:
        # Example: parse tier from entity_id if encoded
        if "alpha" in entity["entity_id"]:
            tier = "α"
            match_origin = "entity_id"
        elif "beta" in entity["entity_id"]:
            tier = "β"
            match_origin = "entity_id"
        elif "gamma" in entity["entity_id"]:
            tier = "γ"
            match_origin = "entity_id"
    if not tier:
        tier, match_origin = tier_classification(
            entity, tier_definitions, fallback_tier="unclassified"
        )
    entity["tier"] = tier
    if "_meta" not in entity:
        entity["_meta"] = {}
    if "inferred_fields" not in entity["_meta"]:
        entity["_meta"]["inferred_fields"] = {}
    # Exemption logic for logic/template/virtual sensors
    if entity.get("sensor_type") in ["logic", "template", "virtual"]:
        entity["tier"] = None
        entity["_meta"]["inferred_fields"]["tier"] = {
            "join_origin": "exemption",
            "join_confidence": 0.0,
            "field_contract": "tier exempted for logic/template/virtual sensor",
            "exemption_reason": f"tier not applicable for {entity.get('sensor_type')} sensor",
        }
    else:
        # Normalize join_origin to the enricher name for consistent provenance
        entity["_meta"]["inferred_fields"]["tier"] = {
            "join_origin": "tier_enricher",
            "join_confidence": 0.9 if tier != "unclassified" else 0.0,
            "field_contract": "tier inferred via tier_definitions",
            "match_origin": match_origin,
        }
    return entity


# Entrypoint for orchestrator
class TierEnricher:
    def __init__(self):
        self.tier_definitions = load_tier_definitions()

    def __call__(self, entity):
        return enrich_entity_with_tier(entity, self.tier_definitions)
