import json
import sys
from typing import Any


def load_json(path: str) -> Any:
    with open(path, "r") as f:
        return json.load(f)


def key_diff(a, b):
    return set(a.keys()) - set(b.keys()), set(b.keys()) - set(a.keys())


def type_mismatch(a, b):
    mismatches = {}
    for k in a:
        if k in b and type(a[k]) != type(b[k]):
            mismatches[k] = (type(a[k]).__name__, type(b[k]).__name__)
    return mismatches


def value_range_violations(a, b):
    # For this mock, just check join_confidence in [0.75, 1.0]
    violations = {}
    if "join_confidence" in a:
        if not (0.75 <= a["join_confidence"] <= 1.0):
            violations["join_confidence"] = a["join_confidence"]
    return violations


def null_or_missing_critical(a, required):
    missing = [k for k in required if k not in a or a[k] is None]
    return missing


def main():
    if len(sys.argv) != 3:
        print(
            "Usage: validate_registry_against_mock.py --output <output.json> --mock <mock.json>"
        )
        sys.exit(2)
    output_path = sys.argv[1]
    mock_path = sys.argv[2]
    output = load_json(output_path)
    mock = load_json(mock_path)
    if not isinstance(output, list) or not isinstance(mock, list):
        print("Both output and mock must be lists of entities.")
        sys.exit(1)
    for i, (o, m) in enumerate(zip(output, mock)):
        print(f"\nEntity {i}:")
        kd1, kd2 = key_diff(o, m)
        if kd1 or kd2:
            print(f"  Key diff: output-only={kd1}, mock-only={kd2}")
        tm = type_mismatch(o, m)
        if tm:
            print(f"  Type mismatches: {tm}")
        vr = value_range_violations(o, m)
        if vr:
            print(f"  Value range violations: {vr}")
        missing = null_or_missing_critical(
            o,
            [
                "entity_id",
                "domain",
                "platform",
                "device_class",
                "entity_category",
                "name",
                "area_id",
                "floor_id",
                "device_id",
                "entry_id",
                "integration",
                "join_confidence",
                "join_origin",
            ],
        )
        if missing:
            print(f"  Null or missing critical fields: {missing}")
    print("\nValidation complete.")


if __name__ == "__main__":
    main()
