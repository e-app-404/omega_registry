from scripts.enrich.enrichers.mobile_app_enricher import MobileAppEnricher


def test_mobile_app_match_existing_device():
    enricher = MobileAppEnricher(create_synthetic=False)
    entity = {
        "entity_id": "sensor.john_phone",
        "platform": "mobile_app",
        "attributes": {"device_id": "phone123"},
    }
    context = {"device_registry": {"dev-1": {"identifiers": ["phone123"]}}}
    out = enricher.enrich(entity, context)
    assert out.get("device_id") == "dev-1"


def test_mobile_app_create_synthetic():
    enricher = MobileAppEnricher(create_synthetic=True)
    entity = {
        "entity_id": "sensor.jane_phone",
        "platform": "mobile_app",
        "attributes": {"owner": "jane"},
    }
    context = {"device_registry": {}}
    out = enricher.enrich(entity, context)
    assert out.get("device_id") == "mobile_app:jane"
