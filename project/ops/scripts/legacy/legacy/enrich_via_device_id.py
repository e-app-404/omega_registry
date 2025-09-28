#!/usr/bin/env python3
"""
Enrich entities with via_device_id from device registry.
Usage: python -m scripts.enrich.enrich_via_device_id --entities <entities.json> --devices <core.device_registry> --output <enriched_entities.json>
"""
import argparse
import json


def build_device_via_map(devices):
    device_via = {}
    for d in devices:
        dev_id = d.get("id")
        via = d.get("via_device_id")
        if dev_id and via is not None:
            device_via[dev_id] = via
    return device_via


def enrich_entities_with_via_device_id(entities, devices):
    """
    Enrich a list of entities with via_device_id from a list of devices.
    Returns a new list of enriched entities.
    """
    device_via_map = build_device_via_map(devices)
    enriched = []
    for e in entities:
        dev_id = e.get("device_id")
        via = device_via_map.get(dev_id)
        if via is not None:
            e["via_device_id"] = via
            e.setdefault("field_inheritance", {})["via_device_id"] = "device_registry"
        enriched.append(e)
    return enriched


def main():
    parser = argparse.ArgumentParser(
        description="Enrich entities with via_device_id from device registry."
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

    enriched = enrich_entities_with_via_device_id(entities, devices)
    with open(args.output, "w") as f:
        json.dump(enriched, f, indent=2)
    print(f"[INFO] Enriched {len(enriched)} entities with via_device_id.")


if __name__ == "__main__":
    main()
