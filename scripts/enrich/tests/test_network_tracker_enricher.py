from scripts.enrich.enrichers.network_tracker_enricher import NetworkTrackerEnricher


def test_network_tracker_match_by_mac():
    enricher = NetworkTrackerEnricher(create_synthetic=False)
    entity = {
        "entity_id": "device_tracker.phone",
        "domain": "device_tracker",
        "platform": "nmap_tracker",
        "attributes": {"mac": "AA:BB:CC"},
    }
    context = {"device_registry": {"dev-1": {"identifiers": ["AA:BB:CC"]}}}
    out = enricher.enrich(entity, context)
    assert out.get("device_id") == "dev-1"


def test_network_tracker_create_synthetic():
    enricher = NetworkTrackerEnricher(create_synthetic=True)
    entity = {
        "entity_id": "device_tracker.guest_phone",
        "domain": "device_tracker",
        "platform": "nmap_tracker",
        "attributes": {"mac": "11:22:33"},
    }
    context = {"device_registry": {}}
    out = enricher.enrich(entity, context)
    assert out.get("device_id") == "net:11:22:33"
