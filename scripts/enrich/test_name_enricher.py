"""
Unit tests for NameEnricher (resolved_name logic)
"""


from scripts.enrich.enrichers.name_enricher import NameEnricher


def make_entity(**kwargs):
    e = {"_meta": {}}
    e.update(kwargs)
    return e


def test_name_priority():
    entity = make_entity(
        name="Kitchen Sensor", original_name="Old Name", entity_id="sensor.kitchen_temp"
    )
    enriched = NameEnricher().enrich(entity, {})
    assert enriched["resolved_name"] == "Kitchen Sensor"
    assert (
        enriched["_meta"]["inferred_fields"]["resolved_name"]["join_origin"] == "name"
    )


def test_original_name_fallback():
    entity = make_entity(original_name="Legacy Name", entity_id="sensor.legacy")
    enriched = NameEnricher().enrich(entity, {})
    assert enriched["resolved_name"] == "Legacy Name"
    assert (
        enriched["_meta"]["inferred_fields"]["resolved_name"]["join_origin"]
        == "original_name"
    )


def test_entity_id_fallback():
    entity = make_entity(entity_id="sensor.living_room_temp")
    enriched = NameEnricher().enrich(entity, {})
    assert enriched["resolved_name"] == "Sensor Living Room Temp"
    assert (
        enriched["_meta"]["inferred_fields"]["resolved_name"]["join_origin"]
        == "entity_id fallback"
    )


def test_no_fields():
    entity = make_entity()
    enriched = NameEnricher().enrich(entity, {})
    assert enriched["resolved_name"] == "Unnamed Entity"
    assert (
        enriched["_meta"]["inferred_fields"]["resolved_name"]["join_origin"]
        == "entity_id fallback"
    )
