"""
hass_architecture.py

Home Assistant architecture and taxonomy definitions for registry, entity, and integration handling.
See support/docs/glossary.md for detailed explanations of each concept.

ARCHITECTURE OVERVIEW
---------------------

Level  | Definition | Examples
------ | ---------- | --------
System (Home Assistant) | The platform that manages and automates your smart home, connecting integrations, devices, and automations. | Home Assistant OS, Core, Supervised
Integration | Code modules that connect Home Assistant to external devices, protocols, services, or APIs. Each integration can provide one or more platforms. | mqtt, esphome, zha, tplink, sonos
Platform | The type of entity that an integration can provide, representing a feature or category (often maps to an entity domain). | For mqtt: sensor, switch, light
Domain | The general class or category of entity, used as the first part of entity IDs and as service namespaces. | sensor, light, switch, climate
Entity | The fundamental units in Home Assistant, representing a single device, sensor, or logical object. | sensor.kitchen_temperature, light.living_room_ceiling
Attribute | Properties and metadata attached to an entity, giving additional context or functionality. | device_class: temperature, unit_of_measurement: °C
Device | Physical or logical devices that may provide one or more entities. | ESP32 board, Z-Wave stick, Hue Bridge
Automation | Logic that triggers actions based on conditions or events. | turn on light at sunset
Script | Reusable sets of actions. | movie time routine
Scene | Snapshots of multiple entities’ states. | romantic dinner lighting

Hierarchy:
Home Assistant
|
|-- Integrations (e.g., mqtt, esphome, zha)
    |
    |-- Platforms (e.g., sensor, switch, light)
        |
        |-- Domains (e.g., sensor, light, switch)
            |
            |-- Entities (e.g., sensor.kitchen_temp)
                |
                |-- Entity Attributes (e.g., device_class, unit_of_measurement)
|
|-- Devices (physical or logical, may have multiple entities)
|
|-- Automations, Scripts, Scenes (logic and orchestration)

Definitions:
- SYSTEM: Home Assistant as a whole (OS, Core, etc.)
- INTEGRATION: Connects to a device/service, provides platforms
- PLATFORM: Type of entity provided by integration (maps to domain)
- DOMAIN: Entity category/type (first part of entity_id)
- ENTITY: Individual object in HA (sensor, light, etc.)
- ATTRIBUTE: Property of entity (device_class, unit_of_measurement, etc.)
- DEVICE: Physical/logical device, may provide multiple entities
- AUTOMATION: Logic to react to triggers
- SCRIPT: Set of actions
- SCENE: Preset states for entities
"""

# === INTEGRATION DOMAINS (from core.config_entries) ===
# HA_INTEGRATIONS: List of all integrations (by domain) found in .storage/core.config_entries.
# Each integration connects Home Assistant to an external system, protocol, or hardware.
HA_INTEGRATIONS = [
    "apple_tv",
    "backup",
    "bluetooth",
    "cast",
    "go2rtc",
    "google_translate",
    "hassio",
    "matter",
    "met",
    "mqtt",
    "radio_browser",
    "raspberry_pi",
    "rpi_power",
    "samsungtv",
    "shopping_list",
    "sonos",
    "sun",
    "thread",
    "tplink",
    "tuya",
    "upnp",
    "withings",
    "wiz",
    "zha",
]

# DOMAINS: List of all entity domains (categories/types) used in the registry. The domain is the first part of an entity_id (e.g., sensor.kitchen_temperature → 'sensor').
# Domains define entity behavior and available services.
HA_DOMAINS = [
    "automation",
    "binary_sensor",
    "button",
    "calendar",
    "climate",
    "counter",
    "cover",
    "dehumidifier",
    "device_tracker",
    "fan",
    "group",
    "humidifier",
    "input_boolean",
    "input_datetime",
    "input_number",
    "input_select",
    "input_text",
    "light",
    "lock",
    "media_player",
    "notify",
    "person",
    "remote",
    "scene",
    "script",
    "sensor",
    "switch",
    "template",
    "vacuum",
    "zone",
]

# STANDARD_DEVICE_CLASSES: List of device classes (subtypes) for domains like sensor and binary_sensor.
# Device class describes the semantic type of the entity (e.g., temperature, humidity, motion).
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

HA_DEFINITIONS = {
    "SYSTEM": "Home Assistant as a whole (OS, Core, etc.)",
    "INTEGRATION": "Connects to a device/service, provides platforms",
    "PLATFORM": "Type of entity provided by integration (maps to domain)",
    "DOMAIN": "Entity category/type (first part of entity_id)",
    "ENTITY": "Individual object in HA (sensor, light, etc.)",
    "ATTRIBUTE": "Property of entity (device_class, unit_of_measurement, etc.)",
    "DEVICE": "Physical/logical device, may provide multiple entities",
    "AUTOMATION": "Logic to react to triggers",
    "SCRIPT": "Set of actions",
    "SCENE": "Preset states for entities",
}

HASS_STORAGE_REGISTRIES = {
    "core.entity_registry": {
        "purpose": "Stores all registered entities in your Home Assistant instance.",
        "structure": "entities[] with fields: entity_id, unique_id, platform, device_id, original_name, original_icon, disabled_by, area_id, ...",
        "use_case": "Links every entity to its origin and device (if any); enables UI/backend to track, rename, enable/disable, or group entities reliably.",
    },
    "core.device_registry": {
        "purpose": "Tracks physical or logical devices that integrations bring in, and groups related entities under these devices.",
        "structure": "devices[] with fields: id, manufacturer, model, sw_version, connections, identifiers, area_id, via_device_id, ...",
        "use_case": "Device pages in UI; grouping all entities from the same hardware; tracking firmware, hardware, and room assignment.",
    },
    "core.area_registry": {
        "purpose": "Defines areas/rooms/zones for organizing devices and entities.",
        "structure": "areas[] with fields: id, name, icon",
        "use_case": "Assign devices/entities to rooms for logical grouping; used in dashboards, automations, and voice assistants for context.",
    },
    "core.config_entries": {
        "purpose": "Tracks all integrations set up in your Home Assistant instance, with their configuration and state.",
        "structure": "entries[] with fields: entry_id, domain, title, source, state, options, ...",
        "use_case": "UI/backend reference for what integrations are configured; used when reloading, removing, or updating integrations.",
    },
    "core.device_automation": {
        "purpose": "Device-based automations.",
        "structure": "Device automation rules.",
        "use_case": "UI automations for devices.",
    },
    "auth": {
        "purpose": "User credentials, tokens, authentication providers.",
        "structure": "Users, tokens.",
        "use_case": "User management, logins, permissions.",
    },
    "auth_provider.homeassistant": {
        "purpose": "User credentials, tokens, authentication providers.",
        "structure": "Users, tokens.",
        "use_case": "User management, logins, permissions.",
    },
    "person": {
        "purpose": "Tracks persons for presence detection.",
        "structure": "id, name, device_trackers, etc.",
        "use_case": "Track presence in the home.",
    },
    "cloud": {
        "purpose": "Stores cloud component config for Home Assistant Cloud/Nabu Casa.",
        "structure": "Cloud connection info.",
        "use_case": "Nabu Casa, cloud integrations.",
    },
    "core.restore_state": {
        "purpose": "Stores last known states of entities for restoring after a restart.",
        "structure": "Entity last states.",
        "use_case": "Restore states on reboot.",
    },
}
