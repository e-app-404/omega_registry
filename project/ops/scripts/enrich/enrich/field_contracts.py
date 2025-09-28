# Field contracts and schema definitions for enrichment normalization

# Anchor/enrichable fields
ANCHOR_FIELDS = ["device_id", "area_id", "floor_id", "platform", "domain", "tier"]


# Profile-relevant field groups
def PROFILE_FIELDS(profile):
    if profile == "slim":
        return ["entity_id", "domain", "platform", "area_id", "device_id"]
    elif profile == "audit":
        return [
            "entity_id",
            "domain",
            "platform",
            "device_class",
            "entity_category",
            "resolved_name",
            "area_id",
            "floor_id",
            "device_id",
            "entry_id",
            "integration",
            "join_confidence",
            "join_origin",
            "tier",
            "labels",
            "serial_number",
            "manufacturer",
            "mac",
            "via_device_id",
            "primary_config_entry",
            "identifiers",
        ]
    else:  # default
        return [
            "entity_id",
            "domain",
            "platform",
            "device_class",
            "entity_category",
            "resolved_name",
            "area_id",
            "floor_id",
            "device_id",
            "entry_id",
            "integration",
            "tier",
            "labels",
        ]


# Enrichment source mappings (join chains, etc.)
JOIN_CHAINS = {
    # Example: 'device_area': [('device_id', 'device_registry', 'area_id')]
}

# Add more as needed for normalization logic
