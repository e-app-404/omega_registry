#!/usr/bin/env python3
"""
Enrich entities with MAC addresses from device registry.
Usage: python -m scripts.enrich.enrich_mac --entities <entities.json> --devices <core.device_registry> --output <enriched_entities.json>
"""
import argparse
import json


def extract_mac(connections):
    if not isinstance(connections, list):
        return None
    for conn in connections:
        if isinstance(conn, (list, tuple)) and len(conn) == 2 and conn[0] == "mac":
            return conn[1].lower()
    return None


def build_device_mac_map(devices):
    device_mac = {}
    for d in devices:
        dev_id = d.get("id")
        mac = extract_mac(d.get("connections", []))
        if dev_id and mac:
            device_mac[dev_id] = mac
    return device_mac


def enrich_entities_with_mac(entities, devices):
    """
    Enrich a list of entities with MAC addresses from a list of devices.
    Returns a new list of enriched entities.
    """
    device_mac_map = build_device_mac_map(devices)
    enriched = []
    for e in entities:
        dev_id = e.get("device_id")
        mac = device_mac_map.get(dev_id)
        if mac:
            e["mac"] = mac
            e.setdefault("field_inheritance", {})["mac"] = "device_registry"
        enriched.append(e)
    return enriched


def main():
    parser = argparse.ArgumentParser(
        description="Enrich entities with MAC addresses from device registry."
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

    device_mac_map = build_device_mac_map(devices)
    enriched = []
    for e in entities:
        dev_id = e.get("device_id")
        mac = device_mac_map.get(dev_id)
        if mac:
            e["mac"] = mac
            # Optionally, add provenance
            e.setdefault("field_inheritance", {})["mac"] = "device_registry"
        enriched.append(e)

    with open(args.output, "w") as f:
        json.dump(enriched, f, indent=2)
    print(f"[INFO] Enriched {len(enriched)} entities with MAC addresses.")


if __name__ == "__main__":
    main()
