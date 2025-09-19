ATTRIBUTE_SYNONYMS = {
    # Frequently stripped or renamed suffixes across domains
    "occupance": "occupancy",
    "contact_sensor": "contact",
    "motion_sensor": "motion",
    "presence_sensor": "presence",
    "config_param": "configuration",
    "illumination": "light_level",
    "connection": "connectivity",
    "battery_level": "battery",
    "sensitivity": "config_sensitivity",
    "timeout": "config_timeout",
    "multipurpose": "sensor_unit",
    "detector": "sensor",  # general fallback
    "monitor": "sensor",
    "update": "firmware",
    "sensor": "",  # used as suffix, often removed
    "param": "configuration",
    "level": "",  # e.g., battery_level
    "media_player": "media_device",
    "alpha": "",
    "omega": "",
    "matter": "",
    "tplink": "",  # protocol suffixes often stripped
    "presence": "occupancy",
    "battery_state": "battery",
    "status_light": "status",
    "signal_strength": "signal",
    "signal_level": "signal",
    "signal_type": "signal",
    "unpair_device": "config_action",
    "firmware_updater": "firmware",
    "energy_saved": "energy",
    "temperature_monitor": "temperature_sensor",
    "humidity_monitor": "humidity_sensor",
}

ROLE_SYNONYMS = {
    # Canonical role mapping for entity usage
    "contact_monitor": "contact_sensor",
    "occupancy_monitor": "occupancy_sensor",
    "motion_monitor": "motion_sensor",
    "presence_monitor": "presence_sensor",
    "light_level_sensor": "illumination_sensor",
    "firmware_updater": "update",
    "config_param": "configuration",
    "battery_monitor": "battery_sensor",
    "ambient_light_sensor": "illumination_sensor",
    "temperature_monitor": "temperature_sensor",
    "media_player": "media_device",
    "configuration": "config_param",  # reverse mapping for clarity
    "connectivity": "connection",
    "signal_monitor": "signal_sensor",
    "humidity_monitor": "humidity_sensor",
}

# === CANONICAL AREA AND FIELD SYNONYMS ===
# These are the canonical definitions for area and field normalization across the Omega Registry pipeline.
AREA_SYNONYMS = {
    # Area name token normalization (name-token fallback support)
    "lounge": "living_room",
    "hall": "hallway",
    "main_bedroom": "bedroom",
    "front_door": "entrance",
    "bathroom": "ensuite",  # if system standardizes around ensuite
    "kitchenette": "kitchen",
    "study": "office",
    "balcony": "outdoor",
    "attic": "loft",
    "garage_entry": "garage",
    "master_bedroom": "bedroom",
    "joels_bedroom": "joel",
    "bedroom_combined": "bedroom",
    "bedroom_desk": "bedroom",
    "bedroom_wardrobe": "bedroom",
    "bedroom_tv_area": "bedroom",
    "hifi_area": "tv_area",
    "hallways": "hallway",
    "livingroom": "living_room",
    "living_room_side": "living_room",
    "living_room_main": "living_room",
    "entrance_door": "entrance",
    "kitchen_corner": "kitchen",
    "laundry_room": "side_kitchen",
}
FIELD_SYNONYMS = {
    "aliases": ["alt_names", "friendly_name"],
    "device_groups": ["group", "device_groups", "area", "room"],
    "integration_stack": ["integration_platform", "integration_platforms", "platform"],
    "protocol_metrics": ["protocol", "protocol_stats", "metrics"],
    "capabilities": ["features", "supported_functions"],
    "history": ["history", "commissioning", "migration", "status_change"],
    "location.room": ["room", "location.room", "room_id"],
    "location.area": ["area", "location.area"],
    "room_area": ["area", "zone", "room_area"],
    "internal_name": ["system_name", "legacy_id", "id"],
    "canonical_id": ["id", "canonical_id"],
    "status": ["status", "device_status"],
    "error_reason": ["last_error", "error_reason"],
    "manufacturer": ["manufacturer"],
    "model": ["model"],
    "identifiers": ["id", "identifiers", "mac_address", "serial_number"],
    # Entity fields
    "entities.state": ["state"],
    "entities.device_class": ["device_class", "type"],
    "entities.unit_of_measurement": ["unit", "unit_of_measurement"],
    "entities.name": ["name", "friendly_name"],
    "entities.domain": ["domain", "type"],
}

# === GREEK TIER TO SYMBOL SYNONYMS ===
# Canonical mapping of greek_tiers to their unicode symbols for registry tier normalization.
GREEK_TIER_SYMBOLS = [
    ("alpha", "α"),
    ("beta", "β"),
    ("chi", "χ"),
    ("delta", "δ"),
    ("epsilon", "ε"),
    ("eta", "η"),
    ("gamma", "γ"),
    ("iota", "ι"),
    ("kappa", "κ"),
    ("lambda", "λ"),
    ("mu", "μ"),
    ("nu", "ν"),
    ("omega", "ω"),
    ("omicron", "ο"),
    ("phi", "φ"),
    ("pi", "π"),
    ("psi", "ψ"),
    ("rho", "ρ"),
    ("sigma", "σ"),
    ("tau", "τ"),
    ("theta", "θ"),
    ("upsilon", "υ"),
    ("xi", "ξ"),
    ("zeta", "ζ"),
]
GREEK_TIER_SYMBOL_MAP = dict(GREEK_TIER_SYMBOLS)


def normalize_attribute(attr):
    if not attr:
        return None
    attr = attr.lower().strip()
    return ATTRIBUTE_SYNONYMS.get(attr, attr)


def normalize_role(role):
    if not role:
        return None
    role = role.lower().strip()
    return ROLE_SYNONYMS.get(role, role)


def normalize_area(area):
    if not area:
        return None
    area = area.lower().strip()
    return AREA_SYNONYMS.get(area, area)


def normalize_slug(slug):
    if not slug:
        return None
    slug = slug.lower().strip()
    # Remove protocol suffixes (alpha, omega, matter, tplink)
    for suffix in ["_alpha", "_omega", "_matter", "_tplink"]:
        if slug.endswith(suffix):
            slug = slug[: -len(suffix)]
    return slug
