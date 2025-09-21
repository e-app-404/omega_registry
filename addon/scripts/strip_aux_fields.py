import json
import sys
from pathlib import Path

AUX_FIELDS = [
    "entity_category",
    "original_device_class",
    "translation_key",
    "options",
    "unit_of_measurement",
    "original_icon",
    "suggested_object_id",
    "previous_unique_id",
]

def strip_aux_fields(entity):
    return {k: v for k, v in entity.items() if k not in AUX_FIELDS}

def main(src, dst):
    with open(src, "r", encoding="utf-8") as f:
        entities = json.load(f)
    stripped = [strip_aux_fields(e) for e in entities]
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(stripped, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: strip_aux_fields.py <src> <dst>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
