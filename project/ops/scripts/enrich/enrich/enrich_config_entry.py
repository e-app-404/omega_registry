#!/usr/bin/env python3
"""
Enrich entities with config entry metadata from core.config_entries via core.device_registry.
Usage: python -m scripts.enrich.enrich_config_entry --entities <core.entity_registry> --devices <core.device_registry> --configs <core.config_entries> --output <enriched_entities.json>
"""
import argparse
import json


def build_device_map(devices):
    return {d["id"]: d for d in devices}


def build_config_map(config_entries):
    return {c["entry_id"]: c for c in config_entries}


def enrich_entities_with_config_metadata(entities, devices, configs):
    """
    Enrich each entity with integration/config entry metadata from device and config registries.
    Adds 'enriched_integrations' (list) and 'multi_integration' (bool) fields to each entity.
    Also propagates 'host' from config entry's data as 'ipv4' if present.
    """
    device_map = build_device_map(devices)
    config_map = build_config_map(configs)
    enriched = []
    for e in entities:
        device_id = e.get("device_id")
        integrations = []
        multi_integration = False
        if device_id and device_id in device_map:
            device = device_map[device_id]
            config_entries_list = device.get("config_entries", [])
            multi_integration = len(config_entries_list) > 1
            for entry_id in config_entries_list:
                cfg = config_map.get(entry_id)
                if cfg:
                    integration = {
                        "integration_domain": cfg.get("domain"),
                        "integration_entry_id": entry_id,
                        "integration_title": cfg.get("title"),
                        "integration_source": cfg.get("source"),
                        "discovery_keys": cfg.get("discovery_keys"),
                        "integration_unique_id": cfg.get("unique_id"),
                        "integration_url": cfg.get("url"),
                    }
                    # PATCH: propagate host as ipv4 if present
                    host = cfg.get("data", {}).get("host")
                    if host:
                        integration["ipv4"] = host
                    integrations.append(integration)
        else:
            # No device: fallback to platform (integration domain guess)
            integrations.append(
                {
                    "integration_domain": e.get("platform"),
                    "integration_entry_id": None,
                    "integration_title": None,
                    "integration_source": None,
                    "discovery_keys": None,
                    "integration_unique_id": None,
                    "integration_url": None,
                }
            )
        e["enriched_integrations"] = integrations
        e["multi_integration"] = multi_integration
        enriched.append(e)
    return enriched


def main():
    parser = argparse.ArgumentParser(
        description="Enrich entities with config entry metadata from core.config_entries via core.device_registry."
    )
    parser.add_argument(
        "--entities", required=True, help="Path to core.entity_registry JSON file"
    )
    parser.add_argument(
        "--devices", required=True, help="Path to core.device_registry JSON file"
    )
    parser.add_argument(
        "--configs", required=True, help="Path to core.config_entries JSON file"
    )
    parser.add_argument(
        "--output", required=True, help="Path to output enriched entities JSON file"
    )
    args = parser.parse_args()

    with open(args.entities) as f:
        entities = json.load(f)
        if (
            isinstance(entities, dict)
            and "data" in entities
            and "entities" in entities["data"]
        ):
            entities = entities["data"]["entities"]
    with open(args.devices) as f:
        devices = json.load(f)
        if (
            isinstance(devices, dict)
            and "data" in devices
            and "devices" in devices["data"]
        ):
            devices = devices["data"]["devices"]
    with open(args.configs) as f:
        configs = json.load(f)
        if (
            isinstance(configs, dict)
            and "data" in configs
            and "entries" in configs["data"]
        ):
            configs = configs["data"]["entries"]

    enriched = enrich_entities_with_config_metadata(entities, devices, configs)
    with open(args.output, "w") as f:
        json.dump(enriched, f, indent=2)
    print(f"[INFO] Enriched {len(enriched)} entities with config entry metadata.")


if __name__ == "__main__":
    main()

# Legacy config entry enrichment logic has been fully migrated to scripts/enrich/enrichers/config_entry_enricher.py.
# This file is now deprecated and safe to remove.
