def normalize_entity_fields(entity: dict) -> dict:
    """
    Normalize and flatten entity fields after enrichment.
    - Flatten identifiers
    - Promote enriched_integrations fields
    - Generate resolved_name
    - Remove redundant fields
    - Ensure _meta.inferred_fields is populated and preserved
    - Preserve all _meta join-related telemetry
    """
    normalized = dict(entity)  # shallow copy to avoid mutating input
    # --- Identifier Field Refactoring ---
    if "identifiers" in normalized and isinstance(normalized["identifiers"], list):
        ids = normalized["identifiers"]
        if len(ids) == 1 and isinstance(ids[0], (list, tuple)) and len(ids[0]) == 2:
            normalized["identifier_type"], normalized["identifier_value"] = ids[0]
            del normalized["identifiers"]
        else:
            import logging

            logging.warning(
                f"Multiple or malformed identifiers for entity_id={normalized.get('entity_id')}; skipping normalization"
            )
    # Promote enriched_integrations
    if (
        "enriched_integrations" in normalized
        and isinstance(normalized["enriched_integrations"], list)
        and normalized["enriched_integrations"]
    ):
        first_integration = normalized["enriched_integrations"][0]
        for k, v in first_integration.items():
            if k not in normalized:
                normalized[k] = v
        # normalized.setdefault("_meta", {}).setdefault("inferred_fields", {})["integration_flattened_fields"] = list(first_integration.keys())
        del normalized["enriched_integrations"]
    # --- Resolved Name Unification ---
    resolved_name = None
    join_origin = None
    join_confidence = 1.0
    field_contract = None
    if "name" in entity and entity["name"]:
        resolved_name = entity["name"]
        join_origin = "name field"
        field_contract = "resolved_name from name"
    elif "original_name" in entity and entity["original_name"]:
        resolved_name = entity["original_name"]
        join_origin = "original_name field"
        field_contract = "resolved_name from original_name"
    elif "entity_id" in entity and isinstance(entity["entity_id"], str):
        # Prefer the full entity_id as the resolved_name to preserve clarity
        # (tests expect 'sensor.x' rather than a title-cased suffix like 'X').
        resolved_name = entity["entity_id"]
        join_origin = "entity_id"
        field_contract = "resolved_name from entity_id"
    else:
        resolved_name = "unknown"
        join_origin = "unresolved"
        join_confidence = 0
        field_contract = "resolved_name could not be inferred"
    normalized["resolved_name"] = resolved_name
    # Track provenance
    meta = normalized.setdefault("_meta", {})
    inferred = meta.setdefault("inferred_fields", {})
    inferred["resolved_name"] = {
        "join_origin": join_origin,
        "join_confidence": join_confidence,
        "field_contract": field_contract,
    }
    # Remove redundant fields
    for redundant in [
        "original_name",
        "has_entity_name",
        "name",
        "suggested_object_id",
    ]:
        if redundant in normalized:
            del normalized[redundant]
    # --- Harden: Always preserve _meta and its subfields ---
    if "_meta" in entity:
        normalized["_meta"] = entity["_meta"]
    else:
        normalized.setdefault("_meta", {}).setdefault("inferred_fields", {})
    # --- Join Provenance Field Roll-Up ---
    import logging

    inferred = normalized.get("_meta", {}).get("inferred_fields", {})
    if inferred:
        join_summary = normalized.setdefault("_meta", {}).setdefault("join_summary", {})
        for field, meta in inferred.items():
            if field in normalized:
                join_summary[field] = {
                    k: meta[k]
                    for k in (
                        "join_origin",
                        "join_confidence",
                        "field_contract",
                    )
                    if k in meta
                }
            else:
                logging.warning(
                    f"[JOIN-ROLLUP] Inferred field '{field}' has provenance but is not present at top level."
                )

    # --- Domain Field Inference & Validation ---
    if not normalized.get("domain"):
        if "entity_id" in normalized and isinstance(normalized["entity_id"], str):
            domain = normalized["entity_id"].split(".")[0]
            normalized["domain"] = domain
            # Track inference in _meta.inferred_fields
            meta = normalized.setdefault("_meta", {})
            inferred = meta.setdefault("inferred_fields", {})
            inferred["domain"] = {
                "join_origin": "entity_id prefix",
                "join_confidence": 1.0,
                "field_contract": "domain inferred from entity_id",
            }
        else:
            # Do not raise here; allow normalization to proceed for entities that
            # don't have an entity_id (tests expect identifier flattening to work
            # even when entity_id/domain cannot be inferred). Record unresolved
            # domain provenance in _meta.inferred_fields.
            meta = normalized.setdefault("_meta", {})
            inferred = meta.setdefault("inferred_fields", {})
            inferred["domain"] = {
                "join_origin": "unresolved",
                "join_confidence": 0,
                "field_contract": "domain could not be inferred",
            }
    # Validate domain only if present
    if "domain" in normalized and (
        not isinstance(normalized["domain"], str) or not normalized["domain"]
    ):
        raise ValueError(
            f"Invalid or missing domain for entity {normalized.get('entity_id')}"
        )

    # --- Canonical Field Order (updated) ---
    from collections import OrderedDict

    canonical_order = [
        "entity_id",
        "resolved_name",
        "domain",
        "platform",
        "tier",
        "area_id",
        "floor_id",
        "device_id",
        "device_name",
        "manufacturer",
        "model",
        "unique_id",
        "integration_domain",
        "integration_entry_id",
        "integration_title",
        "integration_source",
        "config_entry_id",
        "primary_config_entry",
        "identifier_type",
        "identifier_value",
        "multi_integration",
        "created_at",
        "modified_at",
        "supported_features",
        "unit_of_measurement",
        "translation_key",
        "capabilities",
        "labels",
        "_meta",
    ]
    # Build ordered dict
    ordered = OrderedDict()
    for key in canonical_order:
        if key in normalized:
            ordered[key] = normalized[key]
    # Add any remaining fields (not in canonical order), sorted alphabetically, except _meta
    remaining = [
        k for k in normalized.keys() if k not in canonical_order and k != "_meta"
    ]
    for k in sorted(remaining):
        ordered[k] = normalized[k]
    # Always put _meta last (unless already present)
    if "_meta" in normalized and "_meta" not in ordered:
        ordered["_meta"] = normalized["_meta"]
    # Consistency check: warn if field order varies
    if list(ordered.keys()) != canonical_order[: len(ordered.keys())]:
        import logging

        logging.warning(
            f"[FIELD-ORDER] Entity {ordered.get('entity_id')} field order does not match canonical order."
        )

    # --- Label Attribution Heuristic ---
    import re

    def slugify(val):
        val = re.sub(r"[^a-zA-Z0-9]+", "-", str(val).lower()).strip("-")
        return val

    label_sources = [
        normalized.get("resolved_name"),
        normalized.get("platform"),
        normalized.get("domain"),
        normalized.get("integration_domain"),
    ]
    labels = []
    seen = set()
    for src in label_sources:
        if src and isinstance(src, str):
            slug = slugify(src)
            if slug and slug not in seen:
                labels.append(slug)
                seen.add(slug)
    normalized["labels"] = labels
    # Log inference logic
    meta = normalized.setdefault("_meta", {})
    inferred = meta.setdefault("inferred_fields", {})
    inferred["labels"] = {
        "join_origin": "label heuristic",
        "join_confidence": 1.0 if labels else 0,
        "field_contract": "labels from resolved_name, platform, domain, integration_domain",
    }

    # --- Tier Classification Canonical Enforcement ---
    # Validate that tier is one of the canonical set from tier_definitions.yaml
    canonical_tiers = set(["α", "β", "γ", "δ", "ε", "ζ", "η", "μ", "σ", "unclassified"])
    tier_val = normalized.get("tier")
    if tier_val is not None:
        if tier_val not in canonical_tiers:
            import logging

            logging.warning(
                f"[TIER] Entity {normalized.get('entity_id')} has non-canonical tier: {tier_val}"
            )
        # Ensure exclusivity (should only be one tier)
        for t in canonical_tiers:
            if t != tier_val and normalized.get(t):
                raise ValueError(
                    f"Entity {normalized.get('entity_id')} has conflicting tier assignments: {tier_val} and {t}"
                )

    # --- Join Metadata Population ---
    required_enriched_fields = [
        "area_id",
        "floor_id",
        "tier",
        "resolved_name",
        "labels",
        "serial_number",
        "device_name",
        "manufacturer",
    ]
    for field in required_enriched_fields:
        meta = normalized.setdefault("_meta", {})
        inferred = meta.setdefault("inferred_fields", {})
        if field not in inferred:
            inferred[field] = {
                "join_origin": "unresolved",
                "join_confidence": 0,
                "field_contract": f"{field} could not be enriched",
            }

    return ordered
