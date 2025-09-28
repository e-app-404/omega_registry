# constants.py

# === REGISTRY_INPUT_AND_ANCHOR_TYPE_MAPPINGS ===
# Canonical registry file names and anchor types for all core pipeline inputs. Update here to add or rename any registry input.
VALID_ANCHOR_TYPES = [
    "device_registry",
    "entity_registry",
    "area_registry",
    "floor_registry",
    "category_registry",
    "label_registry",
    "integration_registry",
    "state_snapshot",
    "sensor_registry",
    "light_registry",
    "person",
    "counter",
    "exposed_entity",
    "input_boolean",
    "input_datetime",
    "input_number",
    "input_text",
    "trace",
]
# Only files present in canonical/registry_inputs/ are considered core/baseline inputs.
REGISTRY_SOURCE_FILES = {
    "device_registry": "core.device_registry",
    "entity_registry": "core.entity_registry",
    "area_registry": "core.area_registry",
    "floor_registry": "core.floor_registry",
    "category_registry": "core.category_registry",
    "label_registry": "core.label_registry",
    "integration_registry": "core.config_entries",
    "state_snapshot": "core.restore_state",
    "counter": "counter",
    "exposed_entity": "homeassistant.exposed_entities",
    "input_boolean": "input_boolean",
    "input_datetime": "input_datetime",
    "input_number": "input_number",
    "input_text": "input_text",
    "person": "person",
    "trace": "trace.saved_traces",
}
REGISTRY_SINGLE_KEY = {
    "device": "core.device_registry",
    "entity": "core.entity_registry",
    "area": "core.area_registry",
    "floor": "core.floor_registry",
    "category": "core.category_registry",
    "label": "core.label_registry",
    "integration": "core.config_entries",
    "config": "core.config",
    "restore": "core.restore_state",
    "counter": "counter",
    "exposed": "homeassistant.exposed_entities",
    "boolean": "input_boolean",
    "datetime": "input_datetime",
    "number": "input_number",
    "text": "input_text",
    "person": "person",
    "trace": "trace.saved_traces",
}
ANCHOR_TYPE_BY_SOURCE_FILE = {
    "core.device_registry": "device_registry",
    "core.entity_registry": "entity_registry",
    "core.area_registry": "area_registry",
    "core.floor_registry": "floor_registry",
    "core.category_registry": "category_category",
    "core.label_registry": "label_registry",
    "core.config_entries": "integration_registry",
    "core.restore_state": "state_snapshot",
    "counter": "counter",
    "homeassistant.exposed_entities": "exposed_entity",
    "input_boolean": "input_boolean",
    "input_datetime": "input_datetime",
    "input_number": "input_number",
    "input_text": "input_text",
    "person": "person",
    "trace.saved_traces": "trace",
}

# === ENRICHMENT_AND_OUTPUT_PATHS ===
# Centralized output and enrichment file paths for all pipeline stages. Used for writing and reading derived artifacts.
ENRICHMENT_TARGET_PATHS = {
    "device_registry": "canonical/derived_views/enriched.device_registry.json",
    "entity_registry": "canonical/derived_views/enriched.entity_registry.json",
    "area_registry": "canonical/derived_views/enriched.area_registry.json",
    "floor_registry": "canonical/derived_views/enriched.floor_registry.json",
    "metrics": "canonical/logs/analytics/pipeline_metrics.latest.json",
    "generated_subset": "canonical/enrichment_sources/generated/enriched_device_registry_subset.json",
}
ENRICHMENT_SOURCE_MAP = {"ip_mac_index": "mac"}
ENRICHMENT_INPUT_PATH = (
    "canonical/enrichment_sources/generated/enriched_device_registry_subset.json"
)
ENRICHMENT_OUTPUT_PATH = (
    "canonical/enrichment_sources/generated/enriched.device_registry.json"
)
PIPELINE_METRICS_PATH = "canonical/logs/analytics/pipeline_metrics.latest.json"

# === FIELD_AND_AREA_SYNONYMS ===
# Normalization maps for area and field names. Use these to ensure consistent naming across all pipeline logic.
# PATCH-IMPORT-MERGE-SYNONYMS-V1: AREA_SYNONYMS and FIELD_SYNONYMS are now imported from synonyms.py as canonical definitions for normalization.

# === DEVICE_ENTITY_TIER_CLASSIFICATIONS ===
# Standard device classes, Greek tiers, and other entity classification lists for registry and enrichment logic.
# STANDARD_DEVICE_CLASSES: List of device classes (subtypes) for domains like sensor and binary_sensor.
# Device class describes the semantic type of the entity (e.g., temperature, humidity, motion).
# See support/docs/glossary.md for details.
STANDARD_DEVICE_CLASSES = [
    "alarm",
    "battery",
    "button",
    "climate",
    "contact",
    "cover",
    "device_tracker",
    "door",
    "energy",
    "fan",
    "illuminance",
    "light",
    "lock",
    "media_player",
    "motion",
    "occupancy",
    "person",
    "power",
    "presence",
    "humidity",
    "switch",
    "temperature",
    "window",
]
greek_tiers = [
    "alpha",
    "beta",
    "chi",
    "delta",
    "epsilon",
    "eta",
    "gamma",
    "iota",
    "kappa",
    "lambda",
    "mu",
    "nu",
    "omega",
    "omicron",
    "phi",
    "pi",
    "psi",
    "rho",
    "sigma",
    "tau",
    "theta",
    "upsilon",
    "xi",
    "zeta",
]

greek_symbols = [
    "α",
    "β",
    "χ",
    "δ",
    "ε",
    "η",
    "γ",
    "ι",
    "κ",
    "λ",
    "μ",
    "ν",
    "ω",
    "ο",
    "φ",
    "π",
    "ψ",
    "ρ",
    "σ",
    "τ",
    "θ",
    "υ",
    "ξ",
    "ζ",
]

# === INTEGRATION DOMAINS (from core.config_entries) ===
# HA_INTEGRATIONS: List of all integrations (by domain) found in .storage/core.config_entries.
# See support/docs/glossary.md for definitions. Each integration connects Home Assistant to an external system, protocol, or hardware.

# === ROOM_AREA_HIERARCHY_AND_ATTRIBUTES ===
# Lists and mappings for room/area names, attributes, and subareas. Used for spatial reasoning and registry structure.
omega_rooms = [
    "living_room",
    "bedroom",
    "laundry",
    "ensuite",
    "downstairs",
    "upstairs",
    "kitchen",
    "entrance",
    "hallway",
    "powder_room",
]
omega_room_attributes = [
    "id",
    "friendly_name",
    "aliases",
    "type",
    "floor",
    "groups",
    "categories",
    "areas",
    "adjacency",
    "devices",
    "lights",
    "sensors",
    "configuration",
    "metadata",
    "parent_room (optional, only present in some rooms)",
]
omega_bedroom_areas = ["wardrobe", "ottoman", "desk"]
omega_hallway_areas = ["entrance", "upstairs", "downstairs"]
omega_home_areas = ["ground_floor", "top_floor", "hallway"]
omega_subareas = {
    "bedroom": omega_bedroom_areas,
    "hallway": omega_hallway_areas,
    "home": omega_home_areas,
}

# === AREA_HIERARCHY_FROM_YAML ===
# Canonical area containment graph and node relationships, imported from area_hierarchy.yaml. Used for spatial inference and validation.
AREA_CONTAINMENT_GRAPH = {
    "ground_floor": [
        "hallway",
        "kitchen",
        "laundry_room",
        "living_room",
        "powder_room",
    ],
    "top_floor": ["hallway", "upstairs", "bedroom"],
    "hallway": ["downstairs"],
    "downstairs": ["entrance"],
    "bedroom": ["bedroom_main", "wardrobe", "desk"],
    "evert_sanctum": ["bedroom", "ensuite"],
    "hestia": ["ha_addons", "system_admin", "virtual"],
    "home": ["evert", "general"],
    "network": ["home_assistant", "hubs_and_routers", "nas"],
    "outside": ["london"],
    "services": ["alarm", "calendar", "notifications"],
    "sanctum_evert": ["bedroom", "ensuite"],
    "ensuite": None,
    "kitchen": None,
    "laundry_room": None,
    "living_room": None,
    "entrance": None,
    "upstairs": None,
}
AREA_NODE_TYPES = ["area", "subarea", "person", "service"]
AREA_NODE_IDS = [
    "hallway",
    "kitchen",
    "laundry_room",
    "living_room",
    "entrance",
    "downstairs",
    "upstairs",
    "bedroom",
    "bedroom_main",
    "desk",
    "wardrobe",
    "ensuite",
    "evert",
    "calendar",
    "alarm",
    "notifications",
]
AREA_NODE_CONTAINERS = [
    ["area", "hallway", "Hallway"],
    ["area", "kitchen", "Kitchen"],
    ["area", "laundry_room", "Laundry room"],
    ["area", "living_room", "Living Room"],
    ["area", "entrance", "Entrance"],
    ["area", "downstairs", "Downstairs"],
    ["area", "upstairs", "Upstairs"],
    ["area", "bedroom", "Bedroom main"],
    ["area", "bedroom_main", "Bedroom main"],
    ["area", "desk", "Desk"],
    ["area", "wardrobe", "Wardrobe"],
    ["area", "ensuite", "Ensuite"],
    ["area", "evert", "Evert"],
    ["area", "calendar", "Calendar"],
    ["area", "alarm", "Alarm"],
    ["area", "notifications", "Notifications"],
]
AREA_NODE_PARENTS = {
    "hallway": ["ground_floor", "top_floor"],
    "kitchen": ["ground_floor"],
    "laundry_room": ["ground_floor"],
    "living_room": ["ground_floor"],
    "entrance": ["downstairs"],
    "downstairs": ["hallway"],
    "upstairs": ["hallway"],
    "bedroom": ["sanctum_evert"],
    "bedroom_main": ["bedroom"],
    "desk": ["bedroom"],
    "wardrobe": ["bedroom"],
    "ensuite": ["sanctum_evert"],
    "evert": ["outside"],
    "calendar": ["services"],
    "alarm": ["services"],
    "notifications": ["services"],
}

# === OUTPUT_AND_META ===
# Output contract allowlist, meta fields, and canonical output paths for registry emission and validation.
OMEGA_REGISTRY_STRICT_ALLOWLIST = [
    "entity_id",
    "domain",
    "platform",
    "device_class",
    "entity_category",
    "name",
    "area_id",
    "floor_id",
    "device_id",
    "entry_id",
    "integration",
    "join_origin",
    "labels",
    "via_device_id",
    "state_snapshot",
    "exposed_to_assistant",
    "suggested_area",
    "hidden_by",
    "disabled_by",
    "original_name",
    "mac",
    "connections",
    "manufacturer",
    "model",
    "_meta",
    "conflict_id",
    "field_inheritance",
    "tier",
    "floor_ref",
    "room_ref",
    "voice_assistants",
]
OMEGA_ROOM_REG = "canonical/registry_inputs/omega_room_registry.json"
FLOOR_REGISTRY = "canonical/registry_inputs/core.floor_registry"
AREA_REGISTRY = "canonical/registry_inputs/core.area_registry"
METRICS_FILE = "canonical/logs/analytics/pipeline_metrics.latest.json"
ENTITY_SOURCE = "canonical/derived_views/flatmaps/entity_flatmap.json"
OUTPUT_PATH = "canonical/derived_views/alpha_room_registry.json"
META_TITLE = "Alpha Room Registry"
META_DOCUMENT_STRUCTURE = {
    "_meta": "Metadata about this registry file",
    "rooms": "Array of room objects, each with room_id, friendly_name, floor, tier, cluster_size, has_beta, domains",
}
SCRIPT_NAME = "generate_alpha_registry.py"

# === AUDIT_AND_UTILITY ===
# Audit tag templates and utility constants for enrichment, logging, and device/entity typing.
AUDIT_TAG_TEMPLATE = "PATCH-{action}-{category}-{suffix}"
ENRICHMENT_FIELD_LIST = ["ipv4", "hostname", "confidence"]
ENRICHED_DEVICE_OUTPUT_FIELDS = ["device_id", "name", "manufacturer", "model", "mac"]
ENRICHMENT_LOG_PATH = (
    "canonical/enrichment_sources/generated/omega_registry_enrichment.log"
)
ENRICHED_DEVICE_MAP_PATH = (
    "canonical/enrichment_sources/generated/enriched_device_map.json"
)
DEVICE_TRACKER_ENTITY_TYPE = "device_tracker"
SUBJECT_TYPE = "device"
SOURCE_REGISTRY = "ip_mac_index"
