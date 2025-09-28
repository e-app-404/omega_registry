# Home Assistant Core Concepts Glossary

---

## 1. Integration

- **What it is:** The code/component that connects Home Assistant to an external system, protocol, or hardware.
- **Examples:** `esphome`, `mqtt`, `zwave_js`, `tplink`
- **Purpose:** Integrations bring entities into Home Assistant and manage how they’re set up and updated.
- **In configuration:** Usually seen as the domain of a config entry in `.storage/core.config_entries`.

---

## 2. Domain

- **What it is:** The type or category of an entity in Home Assistant.
- **Examples:** `sensor`, `light`, `switch`, `climate`
- **Purpose:** Defines the entity’s behavior, what services are available (like `light.turn_on`), and how it’s displayed in the UI.
- **In entity IDs:** Always the part before the dot in the entity ID:
  `sensor.kitchen_temperature` → `sensor` is the domain

---

## 3. Platform

- **What it is:** The mechanism or “subsystem” under an integration that provides a certain domain of entities.
- **Examples:** `mqtt.sensor`, `mqtt.switch`, `esphome.light`, `template.sensor`
- **Purpose:** It’s the glue between an integration and a domain. For example, the MQTT integration can provide multiple platforms: `mqtt.sensor`, `mqtt.switch`, `mqtt.light`.
- **In entity registry:** Often stored as `platform: mqtt` (indicating this entity is managed by the MQTT integration), and the entity domain tells you the platform (e.g., sensor, switch).

---

## 4. Device Class

- **What it is:** A semantic classification within a domain, describing what kind of thing the entity actually represents.
- **Examples:**
  - For `sensor` domain: `temperature`, `humidity`, `battery`, `power`
  - For `binary_sensor` domain: `motion`, `door`, `window`, `smoke`
- **Purpose:** Tells Home Assistant (and you!) how to treat/display the entity. For example, a sensor with `device_class: temperature` will show a °C/°F icon and use the appropriate unit.
- **In attributes:** Shown as `device_class` in the entity’s attributes:

  ```yaml
  device_class: temperature
  ```

---

## How They Relate (Example)

Let’s look at a single entity:

- `sensor.living_room_temperature`
  - **Integration:** esphome
    (You added an ESPHome device to HA)
  - **Domain:** sensor
    (It’s a sensor entity)
  - **Platform:** esphome.sensor
    (It was provided by the sensor platform of the ESPHome integration)
  - **Device Class:** temperature
    (It measures temperature, so it gets a thermometer icon and °C/°F unit)

---

## Table: Quick Reference

| Term         | What is it?                | Example values         | Where found                        |
|--------------|----------------------------|------------------------|-------------------------------------|
| Integration  | Connects to a system/service | esphome, mqtt         | .storage/core.config_entries        |
| Domain       | Entity category/type       | sensor, light          | First part of entity_id             |
| Platform     | Integration+domain mechanism | mqtt.sensor           | core.entity_registry/code           |
| Device Class | Subtype within a domain    | temperature, door      | Entity attributes (device_class)    |

---

## Home Assistant Architecture: Recursive Breakdown

### 1. Home Assistant (the System)

- **Definition:** The platform that manages and automates your smart home, connecting integrations, devices, and automations.
- **Examples:** Home Assistant OS, Home Assistant Supervised, Home Assistant Container, Home Assistant Core.

### 2. Integrations

- **Definition:** Code modules that connect Home Assistant to external devices, protocols, services, or APIs. Each integration can provide one or more platforms.
- **Examples:**
  - mqtt (connects to MQTT brokers/devices)
  - esphome (manages ESPHome devices)
  - zha (Zigbee Home Automation)
  - tplink (TP-Link smart plugs)
  - sonos (Sonos speakers)
  - google_translate (Text-to-Speech)

### 3. Platforms

- **Definition:** The type of entity that an integration can provide, representing a feature or category (often maps to an entity domain).
- **Examples:**
  - For mqtt: sensor, switch, light, binary_sensor
  - For esphome: sensor, light, switch, climate, fan
  - For zha: sensor, light, switch, lock, binary_sensor

### 4. Domains

- **Definition:** The general class or category of entity, used as the first part of entity IDs and as service namespaces.
- **Examples:**
  - sensor (generic measurement)
  - light (lights)
  - switch (switches)
  - lock (locks)
  - media_player (audio/video devices)
  - climate (thermostats, AC units)
  - vacuum (robot vacuums)
  - person, zone, automation, script, scene (special domains)

### 5. Entities

- **Definition:** The fundamental units in Home Assistant, representing a single device, sensor, or logical object.
- **Examples:**
  - sensor.kitchen_temperature (a temperature sensor)
  - light.living_room_ceiling (a smart light)
  - switch.garage_door (a relay-controlled door)
  - lock.front_door (a smart lock)
  - climate.bedroom (a thermostat)

### 6. Entity Attributes (including device_class)

- **Definition:** Properties and metadata attached to an entity, giving additional context or functionality.
- **Examples:**
  - device_class: Describes the kind of entity (e.g., for a sensor: temperature, humidity, battery)
  - unit_of_measurement: e.g., °C, %, W
  - friendly_name: e.g., "Kitchen Temperature"
  - state_class: e.g., measurement, total_increasing
  - icon: e.g., mdi:thermometer
  - Other: last_changed, last_updated

### Parallel to Platforms/Entities: Devices

- **Definition:** Physical or logical devices that may provide one or more entities. Devices are tracked in the device registry and are typically mapped to integrations.
- **Examples:**
  - A single ESPHome node (esphome.kitchen_sensor)
  - A Hue Bridge (manages multiple Hue bulbs)
  - A Z-Wave stick (manages a mesh of Z-Wave devices)
  - A smart plug (provides switch and power sensor entities)

### Other Architectural Elements

- **Automations**
  - **Definition:** Logic that triggers actions based on conditions or events.
  - **Examples:** Turn on lights at sunset; Notify if a door is left open.
- **Scripts**
  - **Definition:** Reusable sets of actions.
  - **Examples:** “Good Morning” scene (turns on lights, starts coffee, reads weather).
- **Scenes**
  - **Definition:** Snapshots of multiple entities’ states.
  - **Examples:** “Movie Time” (dims lights, turns on TV, sets speakers).

---

### Visualized Hierarchy

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

---

### Summary Table

| Level         | Definition                                   | Examples                                      |
|-------------- |----------------------------------------------|-----------------------------------------------|
| Home Assistant| The system/platform                          | HA OS, HA Core                                |
| Integration   | Connects to a device/service                 | mqtt, esphome, zha, tplink                    |
| Platform      | Type of entity provided by integration        | sensor, switch, light                         |
| Domain        | Entity category/type                         | sensor, light, switch, climate                |
| Entity        | Individual object in HA                      | sensor.living_room_temp, light.kitchen        |
| Attribute     | Property of entity                           | device_class: temperature, unit_of_measurement: °C |
| Device        | Physical/logical device                      | ESP32 board, Z-Wave stick, Hue Bridge         |
| Automation    | Logic to react to triggers                   | turn on light at sunset                       |
| Script        | Set of actions                               | movie time routine                            |
| Scene         | Preset states for entities                   | romantic dinner lighting                      |

---

## Home Assistant .storage Registry Files: Structure, Purpose, and Use Cases

### What is the .storage folder?

- `.storage` is a hidden directory in your Home Assistant config folder.
- It holds persistent configuration data in JSON format for the Home Assistant backend—including registry files, configuration entries, user preferences, and more.
- **Warning:** Don’t edit these files directly unless you really know what you’re doing.

### Core Registry Files Overview

The main registries you’ll interact with are:

1. `core.entity_registry`
2. `core.device_registry`
3. `core.area_registry`
4. `core.config_entries`
5. `core.device_automation`
6. `core.restore_state`
7. `auth`, `auth_provider.homeassistant` (authentication)
8. `cloud`, `person`, and others

#### 1. core.entity_registry

- **Purpose:** Stores all registered entities in your Home Assistant instance.
- **Structure:**
  - `entities[]` with fields: `entity_id`, `unique_id`, `platform`, `device_id`, `original_name`, `original_icon`, `disabled_by`, `area_id`, ...
- **Use Case:** Links every entity to its origin and device (if any); enables UI/backend to track, rename, enable/disable, or group entities reliably.

#### 2. core.device_registry

- **Purpose:** Tracks physical or logical devices that integrations bring in, and groups related entities under these devices.
- **Structure:**
  - `devices[]` with fields: `id`, `manufacturer`, `model`, `sw_version`, `connections`, `identifiers`, `area_id`, `via_device_id`, ...
- **Use Case:** Device pages in UI; grouping all entities from the same hardware; tracking firmware, hardware, and room assignment.

#### 3. core.area_registry

- **Purpose:** Defines areas/rooms/zones for organizing devices and entities.
- **Structure:**
  - `areas[]` with fields: `id`, `name`, `icon`
- **Use Case:** Assign devices/entities to rooms for logical grouping; used in dashboards, automations, and voice assistants for context.

#### 4. core.config_entries

- **Purpose:** Tracks all integrations set up in your Home Assistant instance, with their configuration and state.
- **Structure:**
  - `entries[]` with fields: `entry_id`, `domain`, `title`, `source`, `state`, `options`, ...
- **Use Case:** UI/backend reference for what integrations are configured; used when reloading, removing, or updating integrations.

#### 5. Other Notable Files

- `auth`, `auth_provider.homeassistant`: User credentials, tokens, authentication providers (user management, logins, permissions)
- `person`: Tracks persons for presence detection (id, name, device_trackers, etc.)
- `cloud`: Stores cloud component config for Home Assistant Cloud/Nabu Casa
- `core.restore_state`: Stores last known states of entities for restoring after a restart
- `core.device_automation`: Stores automations directly linked to devices

#### Overview Table

| File                   | Purpose                                 | Main Data Structure/Key Fields                | Use Case / Example                      |
|------------------------|-----------------------------------------|-----------------------------------------------|-----------------------------------------|
| core.entity_registry   | All entities registered in HA           | entities[], entity_id, platform, device_id    | Track, link, and manage all entities    |
| core.device_registry   | All devices (physical/logical) in HA    | devices[], id, manufacturer, area_id          | Group entities, assign to rooms, firmware|
| core.area_registry     | Areas/rooms/zones for organization      | areas[], id, name                            | UI grouping, area assignment            |
| core.config_entries    | Configured integrations                 | entries[], domain, entry_id, state            | Track integrations, reload/remove via UI |
| core.device_automation | Device-based automations                | Device automation rules                       | UI automations for devices              |
| auth, auth_provider.*  | User authentication/authorization       | Users, tokens                                 | User logins, permissions                |
| person                | Person presence tracking                | id, name, device_trackers                     | Track presence in the home              |
| cloud                 | Home Assistant Cloud settings           | Cloud connection info                         | Nabu Casa, cloud integrations           |
| core.restore_state     | Entity state restoration after restart  | Entity last states                            | Restore states on reboot                |

#### Key Points

- The .storage registries are JSON config files, not live state—they persist setup/configuration.
- Entities link to devices (and areas), and both are tracked in their respective registries.
- Integrations are configured in core.config_entries, not tied to individual entities or devices.
- These files are crucial for Home Assistant’s operation and should not be edited directly.

---
