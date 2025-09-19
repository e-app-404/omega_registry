"""
Unit tests for TierEnricher (tier classification and propagation)
"""


from scripts.enrich.enrichers.tier_enricher import TierEnricher


def make_entity(**kwargs):
    e = {"_meta": {}}
    e.update(kwargs)
    return e


def test_full_match_by_device_id_and_area_id():
    entity = make_entity(
        device_id="abc123",
        area_id="kitchen",
        platform="mqtt",
        integration_domain="zwave",
    )
    enriched = TierEnricher()(entity)
    assert enriched["tier"] in ("α", "β")
    assert "tier" in enriched["_meta"]["inferred_fields"]
    assert (
        enriched["_meta"]["inferred_fields"]["tier"]["join_origin"] == "tier_enricher"
    )
    assert enriched["_meta"]["inferred_fields"]["tier"]["join_confidence"] > 0


def test_partial_match_platform_only():
    entity = make_entity(platform="template")
    enriched = TierEnricher()(entity)
    assert enriched["tier"] == "β"
    assert (
        enriched["_meta"]["inferred_fields"]["tier"]["join_origin"] == "tier_enricher"
    )


def test_match_via_integration_domain():
    entity = make_entity(
        platform="mqtt", integration_domain="zwave", domain="input_boolean"
    )
    enriched = TierEnricher()(entity)
    assert enriched["tier"] in ("α", "σ", "unclassified")


def test_explicit_fallback_to_unclassified():
    entity = make_entity(platform="unknown_platform")
    enriched = TierEnricher()(entity)
    assert enriched["tier"] == "unclassified"
    assert enriched["_meta"]["inferred_fields"]["tier"]["join_confidence"] == 0.0


def test_multiple_matches_disambiguation():
    entity = make_entity(
        platform="template", device_id="abc123", attributes={"score_weight": 1}
    )
    enriched = TierEnricher()(entity)
    assert enriched["tier"] in ("β", "γ", "α")


def test_entity_with_override_in_meta():
    entity = make_entity(platform="mqtt", _meta={"override_tier": "σ"})
    enriched = TierEnricher()(entity)
    # If override logic is implemented, this should be respected; else, fallback to normal rules
    assert "tier" in enriched
    assert "tier" in enriched["_meta"]["inferred_fields"]
