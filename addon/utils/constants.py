# DEPRECATED — This file has been merged into registry/utils/. Please update references accordingly.

CLUSTERABLE_DOMAINS = {"binary_sensor", "sensor", "select", "number"}
PROTOCOL_SUFFIXES = {"_alpha", "_omega", "_matter", "_tplink"}
COMMON_AREA_TOKENS = {
    "hall": "hallway",
    "lounge": "living_room",
    "garage_entry": "garage",
    "attic": "loft",
}

# Real values from autocluster_audit.py
COMMON_AREAS = [
    "kitchen", "living_room", "bedroom", "ensuite", "upstairs", "downstairs", "desk", "system_admin", "network_connectivity", "ha_addons", "home", "london"
]

ENTITY_FEATURES = [
    "motion", "presence", "temperature", "humidity", "light", "switch", "door", "window", "occupancy", "illuminance", "contact", "power", "energy", "battery", "fan", "alarm", "button", "lock", "climate", "media_player", "cover"
]

STANDARD_DEVICE_CLASSES = [
    "motion", "presence", "temperature", "humidity", "light", "switch", "door", "window", "occupancy", "illuminance", "contact", "power", "energy", "battery", "fan", "alarm", "button", "lock", "climate", "media_player", "cover"
]

greek_tiers = [
    "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota", "kappa", "lambda", "mu", "nu", "xi", "omicron", "pi", "rho", "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega"
]

ENTITY_ID_SUFFIXES = ['_alpha', '_omega', '_main', '_presence']

SEMANTIC_ROLE_MAP = {
    'occupancy': 'presence_monitor',
    'motion': 'motion_monitor',
    'climate_monitor': 'climate_monitor',
    'humidity_monitor': 'humidity_monitor',
    'contact': 'generic_sensor',
    'multi': 'generic_sensor',
}
