import argparse
import json
import logging
import os
from datetime import datetime
from typing import Optional


def attach_meta(
    source_script: str, contract_tag: str, pipeline_stage: Optional[str] = None
) -> dict:
    meta = {
        "source": source_script,
        "contract": contract_tag,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    if pipeline_stage:
        meta["pipeline_stage"] = pipeline_stage
    return {"_meta": meta}


# PATCH-LOGGING-VALID-JSON-V1
# Utility to write valid JSON logs (array or object), ensuring no trailing commas and proper structure


def write_json_log(filepath, data, mode="w", meta=None):
    """
    Write data to filepath as valid JSON. If meta is provided and data is a dict, merge as {**meta, **data}.
    If mode is 'a', append to a JSON array (create if not exists).
    """
    if meta and isinstance(data, dict):
        # Merge meta and data, but keep meta as _meta key if not already present
        if "_meta" not in data:
            data = {"_meta": meta, **data}
        else:
            data = {**data, "_meta": meta}
    if mode == "w":
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    elif mode == "a":
        # Append to a JSON array in file, or create new array
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                try:
                    arr = json.load(f)
                    if not isinstance(arr, list):
                        arr = [arr]
                except Exception:
                    arr = []
        else:
            arr = []
        arr.append(data)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(arr, f, indent=2, ensure_ascii=False)


def setup_logging(log_path, level=logging.INFO, fmt=None):
    """
    Centralized logging setup. All logs go to canonical/logs/tools/<emitting_script>_<core-function>.log (append-only).
    Echoes the full resolved log file path to the terminal.
    """
    import inspect
    from pathlib import Path

    logs_dir = Path("canonical/logs/tools")
    logs_dir.mkdir(parents=True, exist_ok=True)
    frame = inspect.currentframe()
    caller = inspect.getouterframes(frame)[1]
    script_name = Path(caller.filename).stem
    log_filename = Path(log_path).name
    # Only prepend script_name if not already present
    if not log_filename.startswith(script_name + "_"):
        log_filename = f"{script_name}_{log_filename}"
    centralized_log_path = logs_dir / log_filename
    if fmt is None:
        fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
    logging.basicConfig(
        filename=str(centralized_log_path),
        level=level,
        format=fmt,
        filemode="a",  # append mode
    )
    print(f"[LOGGING] Log file: {centralized_log_path.resolve()}")
    logging.info("Logging started for %s", centralized_log_path.name)


def extract_entities_by_key_value(inp1, inp2, inp3):
    """
    Extract entities from a registry file where entity[inp2] == inp3.
    Args:
        inp1 (str): Source file key (e.g., 'core.entity_registry')
        inp2 (str): Key to filter on (e.g., 'platform')
        inp3 (str): Value to match (e.g., 'smartthings')
    Output:
        Writes filtered entities to canonical/enrichment_sources/generated/inp1.inp2_inp3.json
    """
    import json
    from pathlib import Path

    from scripts.utils.input_list_extract import extract_data

    # Resolve input path from constants
    input_path = Path(f"canonical/registry_inputs/{inp1}")
    output_path = Path(
        f"canonical/enrichment_sources/generated/{inp1}.{inp2}_{inp3}.json"
    )
    log_path = Path(f"canonical/logs/analytics/extract_{inp1}_{inp2}_{inp3}.log")
    setup_logging(log_path)

    with input_path.open() as f:
        core_content = json.load(f)
    core_entities = extract_data(inp1, core_content)

    filtered_entities = [e for e in core_entities if e.get(inp2) == inp3]
    meta = attach_meta(
        source_script=__file__, contract_tag=f"extract_{inp1}_{inp2}_{inp3}"
    )
    print(f"Total entities matching {inp2}={inp3}: {len(filtered_entities)}")
    with output_path.open("w") as f:
        json.dump({"_meta": meta["_meta"], "entities": filtered_entities}, f, indent=2)
    print(f"Exported filtered entities to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract entities by key-value from registry"
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Source file to parse (e.g., core.entity_registry)",
    )
    parser.add_argument(
        "--key", required=True, help="Key to use in the operation (e.g., platform)"
    )
    parser.add_argument(
        "--value", required=True, help="Value to match (e.g., smartthings)"
    )
    args = parser.parse_args()
    extract_entities_by_key_value(args.inp1, args.inp2, args.inp3)


if __name__ == "__main__":
    main()
