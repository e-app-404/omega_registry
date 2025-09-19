# PATCH-REFACTOR-ENRICH-ENGINE  >> This logic is now unified inside enrichment_engine.py via --dry-audit

import json
from pathlib import Path

from scripts.utils.entity_extract import extract_entity_ids_by_platform
from scripts.utils.input_list_extract import extract_data
from scripts.utils.pipeline_config import REGISTRY_SINGLE_KEY


def export_smartthings_entities():
    core_registry_path = Path("canonical/registry_inputs/core.entity_registry")
    output_path = Path(
        f'canonical/enrichment_sources/generated/export.{REGISTRY_SINGLE_KEY["entity"]}.json'
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load and extract entities from core.entity_registry using extract_data
    with core_registry_path.open() as f:
        core_content = json.load(f)
    core_entities = extract_data("core.entity_registry", core_content)

    # Extract all entities with platform 'smartthings'
    smartthings_entity_ids = extract_entity_ids_by_platform(
        core_entities, "smartthings"
    )
    smartthings_entities = [
        e for e in core_entities if e.get("entity_id") in smartthings_entity_ids
    ]

    print(f"Total smartthings entities: {len(smartthings_entities)}")
    with output_path.open("w") as f:
        json.dump(smartthings_entities, f, indent=2)
    print(f"Exported smartthings entities to {output_path}")


def main():
    auto_area_path = Path(
        "canonical/enrichment_sources/generated/auto_area_entities.json"
    )
    core_registry_path = Path("canonical/registry_inputs/core.entity_registry")
    output_path = Path("canonical/core_entity_registry_minus_auto_area.json")

    # Load auto area assignment list
    with auto_area_path.open() as f:
        auto_area = json.load(f)
    auto_ids = set(e["entity_id"] for e in auto_area if "entity_id" in e)

    # Load and extract entities from core.entity_registry using extract_data
    with core_registry_path.open() as f:
        core_content = json.load(f)
    core_entities = extract_data("core.entity_registry", core_content)

    print(f"Total entities in core.entity_registry: {len(core_entities)}")
    print(f"Total entity_ids to subtract: {len(auto_ids)}")

    # Subtract entities present in auto_area list
    filtered = [e for e in core_entities if e.get("entity_id") not in auto_ids]
    print(f"Total entities after subtraction: {len(filtered)}")
    print(
        f"Number of overlapping/matched entity_ids: {len(core_entities) - len(filtered)}"
    )

    # Output using the same structure as the original
    output_data = core_content.copy()
    if "data" in output_data and "entities" in output_data["data"]:
        output_data["data"]["entities"] = filtered
    else:
        output_data = filtered  # fallback for list-rooted registries

    with output_path.open("w") as f:
        json.dump(output_data, f, indent=2)
    print(f"Exported result to {output_path}")


if __name__ == "__main__":
    main()
    export_smartthings_entities()
