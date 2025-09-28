import argparse
import json
import sys
from pathlib import Path

# Use absolute imports if running as module, else fallback to relative
try:
    from scripts.utils.input_list_extract import extract_data
    from scripts.utils.pipeline_config import REGISTRY_SINGLE_KEY
except ImportError:
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from scripts.utils.input_list_extract import extract_data
    from scripts.utils.pipeline_config import REGISTRY_SINGLE_KEY


def export_entities_by_key_value(source_file, key, value):
    """
    Export all entities from the given registry file where entity[key] == value.
    Output: canonical/data_export/<source>.<key>_<value>.json
    """
    core_registry_path = Path(f"canonical/registry_inputs/{source_file}")
    # Use REGISTRY_SINGLE_KEY for brevity in output filename
    source_key = None
    for k, v in REGISTRY_SINGLE_KEY.items():
        if v == source_file or source_file.endswith(v):
            source_key = (
                k if k != "entity" else "entity"
            )  # fallback to 'entity' for core.entity_registry
            break
    if not source_key:
        source_key = source_file.replace("core.", "").replace("_registry", "")
    output_dir = Path("canonical/data_export")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{source_key}.{key}_{value}.json"

    # Load and extract entities from registry using extract_data
    with core_registry_path.open() as f:
        core_content = json.load(f)
    core_entities = extract_data(source_file, core_content)

    filtered_entities = [e for e in core_entities if e.get(key) == value]
    print(f"Total entities matching {key}={value}: {len(filtered_entities)}")
    with output_path.open("w") as f:
        json.dump(filtered_entities, f, indent=2)
    print(f"Exported filtered entities to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export entities by key-value from registry"
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Source file to parse (e.g., core.entity_registry)",
    )
    parser.add_argument(
        "--key",
        required=True,
        help="Key to use in the operation (e.g., platform)",
    )
    parser.add_argument(
        "--value", required=True, help="Value to match (e.g., smartthings)"
    )
    args = parser.parse_args()
    export_entities_by_key_value(args.source, args.key, args.value)
