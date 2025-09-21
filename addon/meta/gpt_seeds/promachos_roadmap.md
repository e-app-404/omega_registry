# 🧭 **Optimized Prompt — PROMACHOS Phase Execution Handoff to Copilot**

## ⚙️ ROLE ACKNOWLEDGMENT

As **Lead Developer**, I take full ownership of result **accuracy**, **empirical grounding**, and **data integrity** across the entity ID remapping and registry rehydration scope.

All **execution tasks** will be delegated to **Copilot**, strictly under my directives.

## 🧱 PROJECT OBJECTIVE

Construct the authoritative `entity_id_migration_map.annotated.v4.json`, using enriched post-reboot artifacts and fingerprinting logic. This map must support:

- Confidence-annotated linking from legacy to post-reboot entity_ids
- Canonical groupings of multi-integration entities into α-tier presence/motion abstractions
- Direct rehydration compatibility with the omega room and alpha sensor registries

## 📍 ROADMAP TO OBJECTIVE

### ✅ Phase 0: Protocol and Execution Setup

- [x] Confirm Promachos and Pythagoras personas loaded
- [x] Validate `system_instruction.yaml` enforcement
- [x] Parse and stage:
  - `omega_device_registry.normalized.enriched.json`
  - Fingerprinting outputs in `fingerprinting_run/`

---

### 🚧 Phase 1: Entity Fingerprint Consolidation

- Aggregate all fingerprint resolutions
- Build canonical `entity_fingerprint_index`
- Cluster entities by:
  - Room
  - Role (`motion`, `occupancy`, `presence`)
  - Integration source (`SmartThings`, `Matter`, `TP-Link`)
- Normalize naming into `[room]_[role]_[entity-function]` format

**Deliverable:** `fingerprint_entity_clusters.v1.json`

---

### 🚧 Phase 2: Confidence-Backed Entity Matchmap

- Derive final mappings using:
  - Last-updated timestamps
  - Unique integration domain signals
  - Area/room-tagged inference (not guesswork)
- Use multiple passes:
  - **Exact match** → area + domain + name alignment
  - **Fuzzy match** → fallback aliases, historic traces
  - **Role inference** → beta-tier function groupings

**Each match will include:**

```json
{
  "pre_reboot_id": "...",
  "post_reboot_id": "...",
  "confidence_score": 0.97,
  "match_method": "area+domain+timestamp+integration",
  "flag_manual_review": false
}

Deliverable: entity_id_migration_map.annotated.v4.json

⸻

🚧 Phase 3: Validation & Risk Check
 • Hard-flag all entries < 0.92 confidence
 • Emit unresolved_entity_candidates.log.json
 • Enforce schema contract for migration map

Deliverable: entity_migration.validation_report.json

⸻

🔒 EXECUTION CONSTRAINTS
 • Zero hallucination tolerance
 • Confidence scores required per output row
 • Empirical basis only: timestamps, fingerprints, room maps, config artifacts
 • No fictional examples or name invention
 • No architecture speculation unless framed as hypothesis

🚩 EXECUTION RISKS

Risk Mitigation
Ambiguous multi-integration overlaps Use fingerprint merge trace + platform signal
Missing pre-reboot ID anchors Trace backward from fingerprint cluster only
Stale sensor aliases or zones Validate against area_id and enriched metadata
Unverifiable mappings Flag as unresolved — defer, don’t guess


⸻

📌 METRICS OF COMPLETION
 • 100% match coverage of all post-reboot sensor entities used in omega room and alpha sensor registries
 • All alpha-tier groupings resolve to concrete post-reboot IDs
 • Validation pass ≥ 95% of entries confidence_score ≥ 0.92

⸻

Now executing the above plan from **Phase 1**.

---

**📣 Copilot:**
Ingest and consolidate the following fingerprinting sources into `fingerprint_entity_clusters.v1.json`:

- Load all JSON, CSV, or Python dataframes in `fingerprinting_run/`
- Construct normalized cluster objects with:
  - `cluster_id` = `[room]_[role]_[entity_function]`
  - List of `post_reboot_entity_ids` belonging to that cluster
  - Associated `integration_sources` and protocol markers
  - Last state timestamps if available

Emit output as JSON file `fingerprint_entity_clusters.v1.json`.
Use empirical timestamps and integration markers to disambiguate when clustering.

🔍 Match Method Priority: `area + domain + integration + timestamp`

When complete, report total number of clusters created and any unresolved entities.

→ Awaiting file outputs or logs to proceed to Phase 2.
