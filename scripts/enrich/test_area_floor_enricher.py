"""
Unit tests for AreaFloorEnricher (area_id and floor_id assignment)
"""


from scripts.enrich.enrichers.area_floor_enricher import AreaFloorEnricher


def make_entity(**kwargs):
    e = {"_meta": {}}
    e.update(kwargs)
    return e


def test_device_to_area_and_floor():
    entity = make_entity(device_id="dev1")
    context = {
        "device_registry": [{"id": "dev1", "area_id": "kitchen"}],
        "area_registry": [{"area_id": "kitchen", "floor_id": "floor1"}],
    }
    enriched = AreaFloorEnricher().enrich(entity, context)
    assert enriched["area_id"] == "kitchen"
    assert enriched["floor_id"] == "floor1"
    assert "area_id" in enriched["_meta"]["inferred_fields"]
    assert "floor_id" in enriched["_meta"]["inferred_fields"]


def test_config_entry_fallback():
    entity = make_entity(config_entry_id="cfg1")
    context = {
        "device_registry": [],
        "config_registry": [{"entry_id": "cfg1", "area_id": "living"}],
        "area_registry": [{"area_id": "living", "floor_id": "floor2"}],
    }
    enriched = AreaFloorEnricher().enrich(entity, context)
    assert enriched["area_id"] == "living"
    assert enriched["floor_id"] == "floor2"


def test_invalid_area_id():
    entity = make_entity(device_id="dev2")
    context = {
        "device_registry": [{"id": "dev2", "area_id": "notreal"}],
        "area_registry": [{"area_id": "kitchen", "floor_id": "floor1"}],
    }
    enriched = AreaFloorEnricher().enrich(entity, context)
    assert "area_id" not in enriched
    assert "floor_id" not in enriched


def test_no_match():
    entity = make_entity(device_id="dev3")
    context = {
        "device_registry": [{"id": "dev2", "area_id": "kitchen"}],
        "area_registry": [{"area_id": "kitchen", "floor_id": "floor1"}],
    }
    enriched = AreaFloorEnricher().enrich(entity, context)
    assert "area_id" not in enriched
    assert "floor_id" not in enriched
