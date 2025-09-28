import json
from pathlib import Path


def write_audit_registry(entities, output_path):
    """
    Write a full audit registry output, including all non-null, non-redundant, and enrichment fields.
    """

    def is_meaningful(key, value):
        if value in (None, "", "null", "none", [], {}, "unclassified"):
            return False
        # Always include these fields if present
        always = {
            "tier",
            "tier_inference_origin",
            "canonical_id",
            "references_entities",
            "attributes_dict",
            "score_weight",
            "formula_type",
            "upstream_sources",
            "file_path",
            "voice_assistants",
            "unique_id",
            "floor_id",
            "created_at",
            "modified_at",
            "unit_of_measurement",
            "entity_category",
            "original_name",
            "aliases",
            "categories",
            "capabilities",
            "config_entry_id",
            "options",
            "original_device_class",
            "translation_key",
            "_meta",
        }
        if key in always:
            return True
        # Also include standard registry fields
        standard = {"entity_id", "domain", "platform", "area_id", "device_id", "name"}
        if key in standard:
            return True
        return True  # fallback: include all non-null fields

    audit_entities = []
    for e in entities:
        audit_e = {k: v for k, v in e.items() if is_meaningful(k, v)}
        audit_entities.append(audit_e)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(audit_entities, f, indent=2, ensure_ascii=False)
