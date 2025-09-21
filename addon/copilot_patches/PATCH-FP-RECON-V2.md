# ✅ Step-by-Step Copilot Instructions

Based on your validation and the newly supplied manual_confirmed_matches.json, we’ll proceed with a series of precise Copilot directives aimed at enhancing cluster inclusion, correcting score alignment, and increasing fingerprint coverage.

⸻

🔧 Step 1: Normalize confidence Field

📣 Copilot: Patch `fingerprint_entity_reconciliation.py`

🔧 GOAL:
Normalize output so that all entries in `entity_fingerprint_map.json` use `confidence_score` instead of `confidence`.

📌 CHANGES:

- After scoring is computed, assign:

```python
  result["confidence_score"] = result.pop("confidence", 0.0)
```

 • Ensure this is consistently applied before dumping the JSON output.

📤 OUTPUT:
 • Updated entity_fingerprint_map.json with confidence_score
 • Log under [PATCH normalize confidence_score field] in conversation_full_history.log

---

## 🧠 **Step 2: Enhance Merge Logic with Fuzzy Area Tolerance**

```copilot
📣 Copilot: Update cluster merging logic to allow for fuzzy area matches

🎯 GOAL:
Let clusters merge if `area_score == 0.0` **but** `name_score + device_class_score + role_score >= 2.5`.

🔧 IN `cluster_merge_trace.py` or wherever merges occur:
- Add logic like:
  ```python
  if area_score == 0.0 and (name_score + device_class_score + role_score) >= 2.5:
      allow_merge = True
      reason = "area mismatch tolerated due to strong feature match"

 • Tag such matches with merge_reason: fuzzy_area_override

📤 OUTPUT:
 • Updated cluster_merge logic
 • cluster_merge_trace.vX.json showing which merges used the override
 • Log under [PATCH fuzzy area override merge logic]

---

### 🧪 **Step 3: Incorporate Manual Confirmed Matches into Training/Scoring Bias**

```copilot
📣 Copilot: Modify scoring logic to learn from `manual_confirmed_matches.json`

🎯 GOAL:
Use manually confirmed mismatches to:
- Penalize patterns that led to rejected matches
- Boost patterns in `manual_confirmed: true`

📌 STRATEGY:
- Load `manual_confirmed_matches.json`
- For each `manual_confirmed: false`, store:
  - `pre_entity_id`, `post_entity_id`, score breakdowns
  - Log a pattern rule that should be penalized
- For `manual_confirmed: true`, add token or domain boost if matched again

📤 OUTPUT:
- Adjusted scoring logic in `fingerprint_entity_reconciliation.py`
- A lookup module like `manual_score_adjustments.py`
- Debug log: `manual_confirmed_adjustment_debug.json`
- Log action under `[PATCH scoring model from manual_confirmed_matches.json]`


⸻

📈 Step 4: Regenerate Clusters and Revalidate

📣 Copilot: Run updated fingerprint_entity_reconciliation.py

✅ Check:
- `entity_fingerprint_map.json` now has `confidence_score` and reweighted scores
- Run `cluster_merge_trace.py` with new merge override logic
- Then run `emit_alpha_sensor_registry.py` to reflect changes

📤 OUTPUT:
- Updated alpha_sensor_registry.json
- Updated `fingerprint_entity_clusters.vX.json`
- Run `audit_cluster_coverage.py` to confirm increased coverage

Log results in `conversation_full_history.log` under `[REBUILD fingerprint pipeline after scoring patch]`
```

⸻

## Followup directives for Copilot

```copilot
📣 Copilot: Confirm patch application and readiness for next steps

✅ PATCH-FP-RECON-V2-001 (Part 1) applied successfully:
 • Confidence normalization is in place (confidence_score)
 • Logging and traceability confirmed via patch_fp_recon_v2_001.log

Proceed with the next step:

▶ `PATCH-FP-RECON-V2-002`: Fuzzy Merge Override Logic

Directive for Copilot:
 • Locate cluster merge logic in `cluster_merge_trace.py` (or wherever clustering occurs)
 • Add override clause:

```python
if area_score == 0.0 and (name_score + device_class_score + role_score) >= 2.5:
    allow_merge = True
    merge_reason = "fuzzy_area_override"
```

 • Ensure merge_reason is logged in cluster_merge_trace.vX.json
 • Emit count of matches that used the override logic
 • Append [`PATCH-FP-RECON-V2-002`] to `conversation_full_history.log`

Acknowledge this directive and confirm when complete.

⸻

## Followup directive for Copilot

```copilot
📣 Copilot: Confirm patch application and readiness for next steps

▶ `PATCH-FP-RECON-V2-003`: Manual Match Bias Adjustment

Directive for Copilot:
 • In `fingerprint_entity_reconciliation.py`, load manual_confirmed_matches.json.
 • For each entry:
 • If manual_confirmed: true: apply a boost to score components (e.g. +0.2)
 • If manual_confirmed: false: apply penalty (e.g. -0.25)
 • Extract match tokens, domains, suffixes, and track patterns.
 • Log:
 • Number of confirmed true / false entries processed
 • Per-pattern adjustments (e.g., domain `media_player.*`penalized)
 • Score deltas before/after
 • Write to:
 • `manual_confirmed_adjustment_debug.json`
 • Append [`PATCH-FP-RECON-V2-003`] to `conversation_full_history.log`

🧠 This step builds intelligence from user-reviewed signals — let me know when to signal Copilot.
```
