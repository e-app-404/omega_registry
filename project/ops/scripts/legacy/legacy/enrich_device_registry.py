#!/usr/bin/env python3
"""
Unified device-level enrichment utility for entities using core.device_registry.
Enriches: manufacturer, device_name, primary_config_entry, identifiers, mac, via_device_id, serial_number.
Provenance for each field is tracked in field_inheritance.
Usage: python -m scripts.enrich.enrich_device_registry --entities <entities.json> --devices <core.device_registry> --output <enriched_entities.json>
"""
import argparse
import json


def build_device_map(devices):
    return {d["id"]: d for d in devices}


def extract_mac(connections):
    if not isinstance(connections, list):
        return None
    for conn in connections:
        if isinstance(conn, (list, tuple)) and len(conn) == 2 and conn[0] == "mac":
            return conn[1].lower()
    return None


def enrich_entities_with_device_fields(entities, devices):
    device_map = build_device_map(devices)
    enriched = []
    for e in entities:
        dev_id = e.get("device_id")
        device = device_map.get(dev_id)
        if device:
            # MAC
            mac = extract_mac(device.get("connections", []))
            if mac:
                e["mac"] = mac
                e.setdefault("field_inheritance", {})["mac"] = "device_registry"
            # via_device_id
            via = device.get("via_device_id")
            if via is not None:
                e["via_device_id"] = via
                e.setdefault("field_inheritance", {})[
                    "via_device_id"
                ] = "device_registry"
            # serial_number
            serial = device.get("serial_number") if "serial_number" in device else None
            e["serial_number"] = serial
            e.setdefault("field_inheritance", {})["serial_number"] = "device_registry"
            # manufacturer
            e["manufacturer"] = device.get("manufacturer")
            # device_name
            name_by_user = device.get("name_by_user")
            name = device.get("name")
            e["device_name"] = (
                name_by_user if name_by_user not in [None, "", "null"] else name
            )
            # primary_config_entry
            e["primary_config_entry"] = device.get("primary_config_entry")
            # identifiers
            e["identifiers"] = device.get("identifiers")
        enriched.append(e)
    return enriched


def main():
    parser = argparse.ArgumentParser(
        description="Unified device-level enrichment utility for entities using core.device_registry."
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

    enriched = enrich_entities_with_device_fields(entities, devices)
    with open(args.output, "w") as f:
        json.dump(enriched, f, indent=2)
    print(f"[INFO] Enriched {len(enriched)} entities with all device-level metadata.")


if __name__ == "__main__":
    main()

# Legacy device registry enrichment logic has been fully migrated to scripts/enrich/enrichers/device_enricher.py.
# This file is now deprecated and safe to remove.
