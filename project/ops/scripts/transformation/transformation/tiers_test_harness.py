from tiers import tier_classification

tier_definitions = {
    "α": {
        "entity_ids": ["sensor.sun_next_dawn"],
        "domain_platforms": [{"domain": "sensor", "platform": "sun"}],
        "entity_id_patterns": ["sensor\\.sun_.*"],
        "platforms": ["sun"],
        "device_classes": [],
    },
    "β": {
        "entity_ids": ["binary_sensor.playstation_4_status"],
        "domain_platforms": [{"domain": "binary_sensor", "platform": "playstation_4"}],
        "entity_id_patterns": ["binary_sensor\\.playstation_4_.*"],
        "platforms": ["playstation_4"],
        "device_classes": [],
    },
}

entities = [
    {
        "entity_id": "sensor.sun_next_dawn",
        "domain": "sensor",
        "platform": "sun",
        "device_class": None,
    },
    {
        "entity_id": "sensor.sun_next_dusk",
        "domain": "sensor",
        "platform": "sun",
        "device_class": None,
    },
    {
        "entity_id": "binary_sensor.playstation_4_status",
        "domain": "binary_sensor",
        "platform": "playstation_4",
        "device_class": None,
    },
    {
        "entity_id": "sensor.unknown",
        "domain": "sensor",
        "platform": "unknown",
        "device_class": None,
    },
    {
        "entity_id": "sensor.bedroom_tv_illuminance_decay_d",
        "domain": "sensor",
        "platform": "template",
        "device_class": None,
    },
]

for entity in entities:
    tier, origin = tier_classification(entity, tier_definitions)
    if tier:
        print(f"[TIER] {entity['entity_id']} assigned to {tier} via {origin}")
    else:
        print(f"[TIER-MISS] {entity['entity_id']} not classified: {origin}")
