# 🧬 CONTEXT SEED: Fingerprinting Strategy for Entity Reconciliation

You are assisting in the reconstruction of a Home Assistant `omega_room_registry` using a combination of **pre-reboot entity groupings** and **post-reboot canonical registry data**.

Due to re-registration during system reboot, most devices and entity IDs have changed, rendering direct ID matching ineffective.

## 🎯 OBJECTIVE

Match pre-reboot entity references (names, domains, roles, rooms) to entities in the new canonical registry (`omega_device_registry.cleaned.v2.json`) using **indirect fingerprinting methods** with a confidence-rated scoring system.

---

## 🔍 ACCEPTED FINGERPRINTING METHODS

You must combine and prioritize the following signals:

### 1. 🔠 Name Similarity (C ≈ 0.85–0.99)

- Use normalized `snake_case` of `entity_id`, `name`, and `friendly_name`
- Apply Levenshtein or Jaro-Winkler distance
- Score highly if:
  - prefix and suffix match (e.g. `bedroom_motion_main_01` → `bedroom_motion_main_alpha`)
  - internal component structures (e.g., `motion`, `temp`, `presence`) align

### 2. 🧱 Domain + Device Class + Unit (C ≈ 0.70–0.95)

- Cross-check the `domain`, `device_class`, and `unit_of_measurement`
- Prefer matches that share both `domain` and `device_class` (e.g., `sensor + humidity`)

### 3. 🏠 Room / Area Association (C ≈ 0.85–1.0)

- Ensure that area mappings match, even if entity IDs don't
- Use `area:` tag, if present in the cleaned registry attributes

### 4. 🔗 Device Clustering / Entity Density (C ≈ 0.60–0.85)

- If 3+ previously linked entities map to the same new device ID, infer the rest are likely co-located
- Apply graph propagation confidence bonus if cluster exceeds 5

### 5. 🧠 Role Mapping via Tier Registry (C ≈ 0.80–0.95)

- Use `alpha_sensor_registry` or `alpha_light_registry` to infer role (motion, presence, temperature, etc.)
- Score higher when roles from pre-reboot entity are reproduced in post-reboot candidate

#### 6. 🕘 Temporal Behavior Correlation (if raw backups available)

- Optional: Compare `last_changed` deltas if state history is available

---

## ⚠️ HALLUCINATION PROTECTION & SCORING

- Set `hallucination_tolerance = 0`
- Assign `confidence_score ∈ [0, 1]` to each fingerprint match
- Flag for manual review if `C < 0.85`
- Flag ambiguous matches if >1 candidate is `C ≥ 0.85` with no clear winner

---

## ✅ DELIVERABLES PER FINGERPRINTING RUN

- `entity_fingerprint_map.json`: map from legacy → new entity with match method + confidence
- `unmatched_entity_trace.json`: list of unresolved or ambiguous entries
- `omega_room_registry.relinked.json`: reconstructed registry using matched entities

---

## 📚 REFERENCE FILES AVAILABLE

- `omega_device_registry.cleaned.v2.json` ← entity source of truth
- `pre-reboot_registry/omega_room_registry.json` ← target layout and groupings
- `alpha_sensor_registry.json`, `alpha_light_registry.json` ← canonical tier and role mappings
- `attribute_purge_remediation.v2.log.json` ← for exclusion auditing
