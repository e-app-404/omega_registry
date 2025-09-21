import sys
import logging
from pathlib import Path
# --- sys.path patch for registry imports ---
project_root = "/Users/evertappels/Projects/omega_registry/addon"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Ensure diagnostics directory exists ---
diag_dir = Path("output/migration_diagnostics")
diag_dir.mkdir(parents=True, exist_ok=True)

# --- Patch 1: Input file presence check ---
FINGERPRINT_PATH = Path("output/fingerprinting_run/entity_fingerprint_map.20250719T112610.json")
PRE_REBOOT_PATH = Path("output/fingerprinting_run/pre_reboot_entities_by_source.json")
missing = []
if not FINGERPRINT_PATH.exists():
    missing.append(str(FINGERPRINT_PATH))
if not PRE_REBOOT_PATH.exists():
    missing.append(str(PRE_REBOOT_PATH))
if missing:
    err_msg = f"[FATAL] Required input file(s) missing: {', '.join(missing)}"
    with open(diag_dir / "rosetta_v5_fatal_error.log", "w") as f:
        import datetime
        f.write(f"[{datetime.datetime.now().isoformat()}] {err_msg}\n")
    print(err_msg)
    sys.exit(1)

# --- Patch 3: Define log_and_print ---
def log_and_print(message):
    print(message)
    logging.info(message)

# --- Patch 2: Initialize per_source_counts ---
per_source_counts = {}

from datetime import datetime
import json
from registry.utils.cluster import make_cluster_id
import time
import signal
from registry.utils.excluded_registry_entities import is_excluded_entity
import argparse
parser = argparse.ArgumentParser(description="Rosetta v5 migration map generator")
parser.add_argument("--verbose_stdout", action="store_true", help="Enable verbose stdout logging (per-entity progress)")
parser.add_argument("--summary", action="store_true", help="Emit only final summary to stdout")
args = parser.parse_args()
VERBOSE_STDOUT = args.verbose_stdout
SUMMARY_ONLY = args.summary

def _timeout_handler(signum, frame):
    raise TimeoutError("Entity match timed out")

signal.signal(signal.SIGALRM, _timeout_handler)

def slugify(s):
    import re
    return re.sub(r'[^a-zA-Z0-9]+', '_', s.strip().lower()) if s else ''

def derive_canonical_key(entity):
    # Try known fields, else slugify entity_id
    for k in ("canonical_entity_key", "internal_name", "entity_id", "name"):
        if k in entity and entity[k]:
            return slugify(entity[k])
    return slugify(str(entity))

# --- Import shared canonical key utilities ---
from shared.utils.canonical_key_utils import derive_shared_canonical_key, compare_keys

# --- Load post-reboot fingerprint map with sun deduplication ---
import glob
# PATCH: Use fingerprint map from input/mappings/entity_fingerprint_map.*.json
fingerprint_candidates = glob.glob("input/mappings/entity_fingerprint_map.*.json")
if not fingerprint_candidates:
    print("[FATAL] No fingerprint map found in input/mappings/")
    sys.exit(1)
FINGERPRINT_PATH = Path(sorted(fingerprint_candidates)[-1])  # Use latest by name
with open(FINGERPRINT_PATH) as f:
    fingerprint_map = json.load(f)

# Patch: Deduplicate sun entities by entity_id
sun_seen = set()
sun_duplicates_dropped = 0
post_candidates = []
for eid, d in fingerprint_map.items():
    shared_key = derive_shared_canonical_key(d)
    if shared_key == "sun":
        if eid in sun_seen:
            sun_duplicates_dropped += 1
            continue
        sun_seen.add(eid)
    post_candidates.append({
        "entity_id": eid,
        "canonical_entity_key": shared_key,
        "original_canonical_key": d.get("canonical_entity_key"),
        "cluster_id": make_cluster_id(d.get("final_area"), d.get("role")),
        "semantic_role": d.get("semantic_role") or d.get("role"),
        "area": d.get("final_area"),
        "role": d.get("role"),
        "aux": {k: d.get(k) for k in ("original_device_class", "entity_category", "translation_key")},
        "raw": d
    })
if sun_duplicates_dropped > 0:
    print(f"[INFO] Deduplicated {sun_duplicates_dropped} duplicate 'sun' entity records by entity_id.")

# --- Load pre-reboot entities from required input file ---
PRE_REBOOT_PATH = Path("output/fingerprinting_run/pre_reboot_entities_by_source.json")
if not PRE_REBOOT_PATH.exists():
    if not SUMMARY_ONLY:
        print(f"[ERROR] Pre-reboot entity file not found at {PRE_REBOOT_PATH}")
    sys.exit(1)
with open(PRE_REBOOT_PATH) as f:
    per_source_entities = json.load(f)
pre_entities = {}
for src, ents in per_source_entities.items():
    for ent in ents:
        key = ent.get("entity_id")
        if key:
            pre_entities[key] = ent

# --- Filtering diagnostics patch ---
filtering_diagnostics = {}
for src, entities in per_source_entities.items():
    parsed = len(entities)
    skipped_missing_entity_id = 0
    excluded_by_is_excluded_entity = 0
    excluded_malformed = 0
    for ent in entities:
        if not isinstance(ent, dict):
            excluded_malformed += 1
            continue
        eid = ent.get("entity_id")
        if not eid:
            skipped_missing_entity_id += 1
            continue
        if is_excluded_entity(eid):
            excluded_by_is_excluded_entity += 1
    filtering_diagnostics[src] = {
        "parsed": parsed,
        "skipped_missing_entity_id": skipped_missing_entity_id,
        "excluded_by_is_excluded_entity": excluded_by_is_excluded_entity,
        "excluded_malformed": excluded_malformed
    }

# Print filtering audit to terminal
print("\n[INFO] Pre-reboot entity filtering diagnostics:")
for src, diag in filtering_diagnostics.items():
    print(f"[INFO] {src}: parsed={diag['parsed']}, skipped_missing_entity_id={diag['skipped_missing_entity_id']}, excluded_by_is_excluded_entity={diag['excluded_by_is_excluded_entity']}, excluded_malformed={diag['excluded_malformed']}")
    net = diag['parsed'] - diag['skipped_missing_entity_id'] - diag['excluded_by_is_excluded_entity'] - diag['excluded_malformed']
    print(f"[INFO]   Net usable entities: {net}")

with open("output/migration_diagnostics/pre_reboot_entity_filtering_diagnostics.json", "w") as f:
    json.dump(filtering_diagnostics, f, indent=2)

# Emit per-source entity counts and combined entity list for diagnostics
import json
with open("output/migration_diagnostics/pre_reboot_entity_per_source_counts.json", "w") as f:
    json.dump(per_source_counts, f, indent=2)
with open("output/migration_diagnostics/pre_reboot_entities_by_source.json", "w") as f:
    json.dump(per_source_entities, f, indent=2)

# Print per-source entity counts to terminal
for src, count in per_source_counts.items():
    print(f"[INFO] Source: {src} -> {count} entities")

# Consistency check
if len(pre_entities) < 0.5 * len(post_candidates):
    log_and_print(f"WARNING: Pre-reboot entity count ({len(pre_entities)}) is much lower than post-reboot ({len(post_candidates)}). Possible data loss or filtering error.")

# --- Matching logic ---
def best_match(pre_info, post_candidates):
    pre_key = derive_shared_canonical_key(pre_info)
    pre_area = pre_info.get("area") or pre_info.get("room") or ""
    pre_role = pre_info.get("role") or pre_info.get("semantic_role") or ""
    pre_aux = {k: pre_info.get(k) for k in ("original_device_class", "entity_category", "translation_key")}
    # Patch: Special-case sun entities
    if pre_key == "sun":
        # Only allow if area, role, and shared_canonical_key are not null
        if not (pre_area and pre_role and pre_key):
            return None, "sun_deduplication", 0.0, "Excluded by sun_deduplication", pre_key, None, 0.0
    # 1. Exact canonical key match
    for cand in post_candidates:
        if pre_key and cand["canonical_entity_key"] == pre_key:
            aux_score = 0.0
            for k in pre_aux:
                if pre_aux[k] and cand["aux"].get(k) and pre_aux[k] == cand["aux"][k]:
                    aux_score += 0.05
                elif pre_aux[k] and cand["aux"].get(k) and pre_aux[k] != cand["aux"][k]:
                    aux_score -= 0.1
            return cand, "exact", min(1.0, 0.98 + aux_score), None, pre_key, cand["canonical_entity_key"], 1.0
    # 2. Fuzzy match using compare_keys
    best = None
    best_score = 0.0
    best_cand_key = None
    for cand in post_candidates:
        score = compare_keys(pre_key, cand["canonical_entity_key"])
        aux_score = 0.0
        for k in pre_aux:
            if pre_aux[k] and cand["aux"].get(k) and pre_aux[k] == cand["aux"][k]:
                aux_score += 0.05
            elif pre_aux[k] and cand["aux"].get(k) and pre_aux[k] != cand["aux"][k]:
                aux_score -= 0.1
        score += aux_score
        if score > best_score:
            best = cand
            best_score = score
            best_cand_key = cand["canonical_entity_key"]
    if best and best_score > 0.85:
        return best, "fuzzy", min(0.97, best_score), None, pre_key, best_cand_key, best_score
    # 3. Role/area/domain alignment
    for cand in post_candidates:
        if pre_role and cand["role"] == pre_role:
            if pre_area and cand["area"] == pre_area:
                return cand, "role_area", 0.85, None, pre_key, cand["canonical_entity_key"], 0.85
    # 4. Slug prefix/partial match
    for cand in post_candidates:
        if pre_key and cand["canonical_entity_key"] and cand["canonical_entity_key"].startswith(pre_key[:6]):
            return cand, "slug_prefix", 0.7, None, pre_key, cand["canonical_entity_key"], 0.7
    # No match
    return None, "unmatched", 0.0, "No suitable match found", pre_key, None, 0.0

def now():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

# --- Build Rosetta migration map ---
# Log sample of pre-entities and post-candidates for inspection (with canonical keys)
def log_sample_entities(pre_entities, post_candidates):
    import json
    pre_sample = []
    for ent in list(pre_entities.values())[:5]:
        pre_sample.append({
            **ent,
            "shared_canonical_key": derive_shared_canonical_key(ent)
        })
    post_sample = []
    for cand in post_candidates[:5]:
        post_sample.append({
            **cand,
            "shared_canonical_key": cand["canonical_entity_key"]
        })
    with open("output/sample_pre_entities.json", "w") as f:
        json.dump(pre_sample, f, indent=2)
    with open("output/sample_post_candidates.json", "w") as f:
        json.dump(post_sample, f, indent=2)
log_sample_entities(pre_entities, post_candidates)

# Remove all references to per_source_counts and log_and_print

# --- Matching loop ---
import time
start_time = time.time()
rosetta_map = []
match_method_summary = {}
confidence_histogram = {}
null_post_count = 0
unmatched_reasons = {}
fallback_method_counts = {"exact": 0, "fuzzy": 0, "role_area": 0, "slug_prefix": 0, "timeout_skipped": 0, "unmatched": 0}
unmatched_entities = []
matched_top10 = []
unmatched_top10 = []

for i, (pre_key, pre_info) in enumerate(pre_entities.items()):
    match_factors = []
    try:
        cand, method, conf, reason, derived_pre_key, derived_post_key, key_score = best_match(pre_info, post_candidates)
    except Exception as e:
        cand = None
        method = "exception"
        conf = 0.0
        reason = str(e)
        derived_pre_key = derive_shared_canonical_key(pre_info)
        derived_post_key = None
        key_score = 0.0
    if cand:
        post_id = cand["entity_id"]
        cluster_id = cand["cluster_id"]
        semantic_role = cand["semantic_role"]
    else:
        post_id = None
        cluster_id = None
        semantic_role = None
        null_post_count += 1
        unmatched_reasons[reason] = unmatched_reasons.get(reason, 0) + 1
        unmatched_entities.append({"pre_key": pre_key, "pre_info": pre_info, "reason": reason, "derived_pre_key": derived_pre_key})
    flag_manual_review = conf < 0.92
    # Patch: Add sun_deduplication diagnostic
    sun_deduplication = (method == "sun_deduplication")
    entry = {
        "pre_reboot_entity_id": pre_info.get("entity_id", pre_key),
        "post_reboot_entity_id": post_id,
        "original_canonical_key": pre_info.get("canonical_entity_key"),
        "derived_canonical_key": derived_pre_key,
        "matched_post_canonical_key": derived_post_key,
        "key_comparison_score": round(key_score, 3),
        "cluster_id": cluster_id,
        "semantic_role": semantic_role,
        "match_method": method,
        "confidence_score": round(conf, 3),
        "source_entity_id": None,
        "flag_manual_review": flag_manual_review,
        "reason": reason,
        "match_factors": match_factors,
        "sun_deduplication": sun_deduplication
    }
    rosetta_map.append(entry)
    match_method_summary[method] = match_method_summary.get(method, 0) + 1
    bucket = str(round(conf, 2))
    confidence_histogram[bucket] = confidence_histogram.get(bucket, 0) + 1
    # Collect top matches and top unmatched for diagnostics
    if method in ("exact", "fuzzy") and len(matched_top10) < 10:
        matched_top10.append(entry)
    if method == "unmatched" and len(unmatched_top10) < 10:
        unmatched_top10.append(entry)

# --- Emit diagnostics and summary files ---
import json
from pathlib import Path

diag_dir = Path("output/migration_diagnostics")
diag_dir.mkdir(parents=True, exist_ok=True)

with open(diag_dir / "matched_top10.json", "w") as f:
    json.dump(matched_top10, f, indent=2)
with open(diag_dir / "unmatched_top10.json", "w") as f:
    json.dump(unmatched_top10, f, indent=2)
with open(diag_dir / "unmatched_pre_reboot_entities.json", "w") as f:
    json.dump(unmatched_entities, f, indent=2)

run_time = time.time() - start_time
run_summary = {
    "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "total_pre_reboot_entities": len(pre_entities),
    "total_mapped": len(rosetta_map) - null_post_count,
    "total_unmatched": null_post_count,
    "match_method_summary": match_method_summary,
    "confidence_histogram": confidence_histogram,
    "top_unmatched_reasons": sorted(unmatched_reasons.items(), key=lambda x: -x[1])[:5],
    "execution_time_sec": round(run_time, 2),
    "match_success_ratio": (len(rosetta_map) - null_post_count) / max(1, len(pre_entities))
}
with open(diag_dir / "rosetta_v5_run_summary.log", "w") as f:
    for k, v in run_summary.items():
        f.write(f"{k}: {v}\n")
with open(diag_dir / "rosetta_v5_match_summary.json", "w") as f:
    json.dump(run_summary, f, indent=2)

# Copy canonical alignment diagnostics if available
import shutil
if Path("output/canonical_alignment_diagnostics.json").exists():
    shutil.copy("output/canonical_alignment_diagnostics.json", diag_dir / "canonical_alignment_diagnostics.json")
if Path("output/canonical_alignment_summary.log").exists():
    shutil.copy("output/canonical_alignment_summary.log", diag_dir / "canonical_alignment_summary.log")

# PATCH: Output migration map to output/mappings/
MIGRATION_MAP_PATH = Path("output/mappings/entity_id_migration_map.rosetta.v5.json")
with open(MIGRATION_MAP_PATH, "w") as f:
    json.dump(rosetta_map, f, indent=2)

# PATCH: Append metrics block to data/pipeline_run_snapshot.20250719T020000.yaml
import yaml
SNAPSHOT_PATH = Path("data/pipeline_run_snapshot.20250719T020000.yaml")
if SNAPSHOT_PATH.exists():
    with open(SNAPSHOT_PATH) as f:
        snapshot = yaml.safe_load(f)
else:
    snapshot = {}
metrics_block = {
    'total_pre_reboot_entities': len(pre_entities),
    'total_matched': sum(1 for m in rosetta_map if m.get('post_reboot_entity_id')),
    'total_unmatched': sum(1 for m in rosetta_map if not m.get('post_reboot_entity_id')),
    'match_method_histogram': match_method_summary,
    'confidence_score_histogram': confidence_histogram,
}
snapshot.setdefault('phase8_metrics', metrics_block)
with open(SNAPSHOT_PATH, 'w') as f:
    yaml.safe_dump(snapshot, f)

# Only print summary if --summary or --verbose_stdout is set
if SUMMARY_ONLY or VERBOSE_STDOUT:
    print(f"\n[SUMMARY] Migration map written to: {MIGRATION_MAP_PATH}")
    print(f"[SUMMARY] Total pre-reboot entities: {len(pre_entities)}")
    print(f"[SUMMARY] Total mapped: {len(rosetta_map) - null_post_count}")
    print(f"[SUMMARY] Total unmatched: {null_post_count}")
    print(f"[SUMMARY] Match method histogram: {match_method_summary}")
    print(f"[SUMMARY] Confidence histogram: {confidence_histogram}")
    print(f"[SUMMARY] Execution time: {run_time:.2f}s")
    print(f"[SUMMARY] Match success ratio: {run_summary['match_success_ratio']:.3f}")
