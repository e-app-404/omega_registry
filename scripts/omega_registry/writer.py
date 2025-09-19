"""
PATCH-OMEGA-REGISTRY-REFACTOR-V1: Writer logic for omega registry output.
Handles deduplication, compaction, and final write to file.
"""

from pathlib import Path

import yaml

from scripts.utils.registry import write_json_compact

PROFILE_YAML_PATH = Path("canonical/support/contracts/registry_output_profiles.yaml")


def load_output_profiles(profile_yaml_path=PROFILE_YAML_PATH):
    with open(profile_yaml_path, "r") as f:
        return yaml.safe_load(f)["output_profiles"]


def filter_entity_by_profile(entity, profile_spec):
    allowlist = profile_spec.get("allowlist", [])
    filtered = {k: v for k, v in entity.items() if k in allowlist}
    # Handle _meta filtering
    if "_meta" in filtered and isinstance(filtered["_meta"], dict):
        meta_spec = profile_spec.get("meta", {})
        if meta_spec.get("include") == "*":
            pass  # keep all meta fields
        else:
            include = meta_spec.get("include", [])
            filtered["_meta"] = {
                k: v for k, v in filtered["_meta"].items() if k in include
            }
        # Optionally add per_field_inference, join_chain_trace, etc. as needed
    return filtered


def deduplicate_entities(entities):
    seen = set()
    unique = []
    for e in entities:
        if not isinstance(e, dict):
            print(f"[WARN] Skipping non-dict entity: {repr(e)[:80]}")
            continue
        eid = e.get("entity_id")
        if eid and eid not in seen:
            unique.append(e)
            seen.add(eid)
    return unique


def write_registry(
    entities, output_path, profile="default", profile_yaml_path=PROFILE_YAML_PATH
):
    profiles = load_output_profiles(profile_yaml_path)
    if profile not in profiles:
        print(f"[WARN] Unknown output profile '{profile}', falling back to 'default'.")
        profile = "default"
    profile_spec = profiles[profile]
    print(f"[INFO] Using output profile: {profile}")
    print(f"[INFO] Profile allowlist: {profile_spec.get('allowlist')}")
    filtered_entities = [filter_entity_by_profile(e, profile_spec) for e in entities]
    write_json_compact(filtered_entities, output_path)
