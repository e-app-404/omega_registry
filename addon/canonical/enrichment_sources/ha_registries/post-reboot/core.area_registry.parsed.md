# Home Assistant core.area_registry — Configuration Analysis Summary

## Schema Observed

Each area object includes:
 • id: Unique area identifier (used in registry bindings)
 • name: Display name
 • floor_id: Semantic or spatial grouping identifier (optional)
 • icon: Optional icon (visual grouping)
 • aliases: Alternate names for UI or logic referencing
 • humidity_entity_id / temperature_entity_id: Optional sensor anchors (currently null)
 • created_at, modified_at: Metadata timestamps

⸻

## Observed Area Classification

🛏 Physical Rooms (User-Oriented)

These represent actual, sensorized or inhabitant-facing rooms.

Area id Name Floor ID
bedroom Bedroom bedroom_evert
kitchen Kitchen null
living_room Living Room null
ensuite Ensuite bedroom_evert
laundry laundry downstairs
laundry_room Laundry room null
wardrobe Wardrobe bedroom_evert
desk Desk bedroom_evert
hallway Hallway null

🧠 These are primary rooms for alpha/omega occupancy, presence, and comfort sensor grouping.

⸻

## Floor Groupings (floor_id)

Defines logical tiers for area hierarchy:

Floor ID Associated Area(s)
bedroom_evert Bedroom, Ensuite, Desk, Wardrobe
downstairs Downstairs, Laundry
upstairs Upstairs
network Home Assistant
hestia Network & Connectivity, Home, System Admin, HA Addons, NAS, Virtual

🧱 These floor_ids act as semantic or architectural clusters for composite grouping, not strictly geometric floors.

⸻

## Abstract / Virtual Zones

These abstract groupings are non-physical, intended to isolate:
 • system-level sensors
 • integrations
 • diagnostics

Area id Purpose
network_connectivity Monitors cloud/integration states
system_admin Logic-level administration zones
ha_addons Addon states, update sensors
virtual Non-physical automations or proxies
nas Synology/server hardware
home_assistant Internal system probes
home Possibly umbrella “global home”
apple_matuvu Named virtual/unknown grouping
evert Reserved placeholder or persona area

🧠 These will NOT generate alpha-tier occupancy/presence groups but may produce virtual diagnostics or inference outputs.

⸻

## CONFIG LAYOUT: KEY FINDINGS

🔹 1. Mixed Semantic Layers
 • Physical vs logical zones coexist (e.g., bedroom vs virtual)
 • System-level zones are declared with hestia or network as floor_id

🔹 2. Floor ID Acts as Tier Linker
 • Allows grouping of related spaces (e.g., all bedroom_evert areas)
 • May influence how shared presence/comfort signals are fused

🔹 3. No Duplication of Rooms
 • Each id is unique and not repeated across aliases
 • Aliases used for hallway labeling only

🔹 4. Area Granularity is High
 • desk, wardrobe, and ensuite are distinct even within bedroom
 • This allows precision-scoped presence logic (e.g., wardrobe_presence_omega)

⸻

## Phase 3 Implications: Alpha Sensor Registry

 • Primary Alpha Groups should only be created for physical/inhabited areas
 • Clustered sensor logic must prefer floor_id when no explicit room match is found
 • Abstract zones may serve as targets for system_occupancy, network_status, or meta_diagnostics groups — but must not conflict with physical alpha sensor groups

⸻

## Summary of Canonical Room Anchors for α-Tier Logic

Area ID Use for Alpha Grouping? Notes
bedroom ✅ Yes Core sleep/occupancy logic
ensuite ✅ Yes Bathroom sensors
desk ✅ Yes Desk-specific presence logic
wardrobe ✅ Yes Often low-signal area
kitchen ✅ Yes Core motion/temp zone
living_room ✅ Yes Comfort and entertainment
laundry ✅ Yes Standalone occupancy zone
laundry_room ✅ Yes (if active) May be duplicate or fallback
hallway ✅ Yes Transitional presence only
upstairs ⚠️ Only for eta-tier Aggregation tier
home, network_connectivity, virtual ❌ Abstract/system-tier only

⸻
