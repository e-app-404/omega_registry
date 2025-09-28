#!/usr/bin/env python3
"""
Enrich entities with serial_number from device registry.
Usage: python -m scripts.enrich.enrich_serial --entities <entities.json> --devices <core.device_registry> --output <enriched_entities.json>
"""
import argparse
import json


def build_device_serial_map(devices):
    device_serial = {}
    for d in devices:
        dev_id = d.get("id")
        serial = d.get("serial_number") if "serial_number" in d else None
        if dev_id:
            device_serial[dev_id] = serial  # Propagate null if missing
    return device_serial


def enrich_entities_with_serial_number(entities, devices):
    """
    Enrich a list of entities with serial_number from a list of devices.
    Returns a new list of enriched entities.
    """
    device_serial_map = build_device_serial_map(devices)
    enriched = []
    for e in entities:
        dev_id = e.get("device_id")
        serial = device_serial_map.get(dev_id)
        e["serial_number"] = serial  # Propagate null if not found
        e.setdefault("field_inheritance", {})["serial_number"] = "device_registry"
        enriched.append(e)
    return enriched


def main():
    parser = argparse.ArgumentParser(
        description="Enrich entities with serial_number from device registry."
    )
    parser.add_argument("--entities", required=True, help="Path to entities JSON file")
    parser.add_argument(
        "--devices", required=True, help="Path to core.device_registry JSON file"
    )
    parser.add_argument(
        "--output", required=True, help="Path to output enriched entities JSON file"
    )
    args = parser.parse_args()

    with open(args.devices) as f:
        devices = json.load(f)
        if (
            isinstance(devices, dict)
            and "data" in devices
            and "devices" in devices["data"]
        ):
            devices = devices["data"]["devices"]
    with open(args.entities) as f:
        entities = json.load(f)
        if isinstance(entities, dict) and "entities" in entities:
            entities = entities["entities"]

    enriched = enrich_entities_with_serial_number(entities, devices)
    with open(args.output, "w") as f:
        json.dump(enriched, f, indent=2)
    print(f"[INFO] Enriched {len(enriched)} entities with serial_number.")


if __name__ == "__main__":
    main()
