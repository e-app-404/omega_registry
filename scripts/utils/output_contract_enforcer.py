import argparse
import json
import os
import sys
from typing import Any

from scripts.utils.loaders import load_yaml


def load_json(path: str) -> Any:
    with open(path, "r") as f:
        return json.load(f)


def check_file_exists(path: str) -> bool:
    return os.path.exists(path)


def check_file_not_empty(path: str) -> bool:
    return os.path.getsize(path) > 0


def check_min_entries(path: str, min_entries: int) -> bool:
    try:
        if path.endswith(".json"):
            data = load_json(path)
            if isinstance(data, list):
                return len(data) >= min_entries
            elif isinstance(data, dict):
                return len(data) >= min_entries
        elif path.endswith(".yaml") or path.endswith(".yml"):
            data = load_yaml(path)
            if isinstance(data, list):
                return len(data) >= min_entries
            elif isinstance(data, dict):
                return len(data) >= min_entries
    except Exception:
        return False
    return False


def check_required_keys(path: str, required_keys: list) -> bool:
    try:
        if path.endswith(".json"):
            data = load_json(path)
        else:
            data = load_yaml(path)
        if isinstance(data, list):
            for entry in data:
                if not all(k in entry for k in required_keys):
                    return False
        elif isinstance(data, dict):
            for entry in data.values():
                if isinstance(entry, dict):
                    if not all(k in entry for k in required_keys):
                        return False
        else:
            return False
        return True
    except Exception:
        return False


def log_failure(msg: str, contract_path: str):
    import datetime

    log_dir = "canonical/logs/scratch"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(
        log_dir,
        f'CONTRACT-ENFORCEMENT-FAILURES-{datetime.datetime.now().strftime("%Y%m%dT%H%M%S")}.log',
    )
    with open(log_path, "a") as f:
        f.write(f"{msg}\nContract: {contract_path}\n")
    print(f"[CONTRACT ENFORCEMENT FAILURE] {msg} (see {log_path})")


def enforce_contract(contract_path: str):
    contract = load_yaml(contract_path)
    all_passed = True
    for output in contract.get("outputs", []):
        path = output["path"]
        if output.get("must_exist", False) and not check_file_exists(path):
            log_failure(f"File missing: {path}", contract_path)
            all_passed = False
            continue
        if output.get("must_contain", False) and not check_file_not_empty(path):
            log_failure(f"File empty: {path}", contract_path)
            all_passed = False
        if "min_entries" in output and not check_min_entries(
            path, output["min_entries"]
        ):
            log_failure(
                f'File {path} has fewer than {output["min_entries"]} entries',
                contract_path,
            )
            all_passed = False
        if "required_keys" in output and not check_required_keys(
            path, output["required_keys"]
        ):
            log_failure(
                f'File {path} missing required keys: {output["required_keys"]}',
                contract_path,
            )
            all_passed = False
    if not all_passed:
        sys.exit(1)
    print("[CONTRACT ENFORCEMENT] All output contracts passed.")


def run_structural_diff(output_path, reference_path):
    import json

    with open(output_path) as f1, open(reference_path) as f2:
        out = json.load(f1)
        ref = json.load(f2)
    if not isinstance(out, list) or not isinstance(ref, list):
        print("[MOCK DIFF] Both output and reference must be lists of entities.")
        return
    for i, (o, m) in enumerate(zip(out, ref)):
        ko = set(o.keys())
        km = set(m.keys())
        kd1 = ko - km
        kd2 = km - ko
        if kd1 or kd2:
            print(f"[MOCK DIFF] Entity {i}: output-only={kd1}, mock-only={kd2}")
        for k in o:
            if k in m and type(o[k]) != type(m[k]):
                print(
                    f"[MOCK DIFF] Entity {i}: Type mismatch for {k}: {type(o[k]).__name__} vs {type(m[k]).__name__}"
                )
        if "join_confidence" in o and not (0.75 <= o["join_confidence"] <= 1.0):
            print(
                f"[MOCK DIFF] Entity {i}: join_confidence out of range: {o['join_confidence']}"
            )
        missing = [
            k
            for k in [
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
            ]
            if k not in o or o[k] is None
        ]
        if missing:
            print(f"[MOCK DIFF] Entity {i}: Null or missing critical fields: {missing}")
    print("[MOCK DIFF] Structural diff complete.")


# Contract validation logic is generic and supports new sources/outputs as long as contract YAML is updated.
# Ensure required_keys and outputs in contract YAML are up to date for new sources.

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("contract", nargs="?")
    parser.add_argument(
        "--reference_snapshot", help="Path to mock reference snapshot for diff"
    )
    args = parser.parse_args()
    if not args.contract:
        print(
            "Usage: python output_contract_enforcer.py <contract.yaml> [--reference_snapshot <mock.json>]"
        )
        sys.exit(2)
    enforce_contract(args.contract)
    # If validating omega_registry_master.json, require --reference_snapshot
    contract = load_yaml(args.contract)
    for output in contract.get("outputs", []):
        if output["path"].endswith("omega_registry_master.json"):
            if not args.reference_snapshot:
                print(
                    "Error: --reference_snapshot is required when validating omega_registry_master.json"
                )
                sys.exit(2)
            run_structural_diff(output["path"], args.reference_snapshot)
