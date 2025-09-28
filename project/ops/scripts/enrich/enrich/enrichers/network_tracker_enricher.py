import logging


class NetworkTrackerEnricher:
    """Enricher for network-based device_tracker entities (nmap_tracker, ping).

    Behavior:
    - Inspect attributes for mac_address, ip, host_name and attempt to match core.device_registry
    - If a match is found, attach device_id
    - Optionally create a synthetic device record if no match
    """

    def __init__(self, create_synthetic=False):
        self.create_synthetic = create_synthetic

    def enrich(self, entity, context):
        if entity.get("domain") != "device_tracker":
            return entity

        platform = entity.get("platform")
        if platform not in ("nmap_tracker", "ping"):
            return entity

        attrs = entity.get("attributes", {}) or {}
        mac = attrs.get("mac") or attrs.get("mac_address") or attrs.get("macaddr")
        ip = attrs.get("ip") or attrs.get("ip_address") or attrs.get("ipv4")

        # try matching in provided device_registry (dict device_id->device obj)
        devmap = {}
        if "device_registry" in context:
            raw = context["device_registry"]
            if isinstance(raw, dict):
                devmap = raw
            elif isinstance(raw, list):
                for idx, entry in enumerate(raw):
                    if not isinstance(entry, dict):
                        logging.warning(
                            "Skipping non-dict device_registry entry at index %s",
                            idx,
                        )
                        continue
                    did = (
                        entry.get("device_id")
                        or entry.get("id")
                        or entry.get("_id")
                        or f"dev-{idx}"
                    )
                    devmap[did] = entry
            else:
                logging.warning(
                    "device_registry in context is not dict or list; skipping device matching"
                )

            for did, dev in devmap.items():
                if not isinstance(dev, dict):
                    logging.warning("Skipping non-dict device entry for id %s", did)
                    continue
                identifiers = dev.get("identifiers") or []
                # identifiers may have MAC or other known values
                if mac and mac in identifiers:
                    entity["device_id"] = did
                    entity.setdefault("_meta", {}).setdefault("inferred_fields", {})[
                        "device_id"
                    ] = {
                        "join_origin": "network_tracker_enricher",
                        "join_confidence": 0.95,
                        "field_contract": "matched device by MAC in device_registry",
                    }
                    return entity
                # Also check if ip is recorded in device records
                if ip and any(ip == str(x) for x in (dev.get("ip_addresses") or [])):
                    entity["device_id"] = did
                    entity.setdefault("_meta", {}).setdefault("inferred_fields", {})[
                        "device_id"
                    ] = {
                        "join_origin": "network_tracker_enricher",
                        "join_confidence": 0.8,
                        "field_contract": "matched device by IP in device_registry",
                    }
                    return entity

        # if no match and synthetic creation allowed, create synthetic device id using mac or ip
        if self.create_synthetic:
            key = mac or ip or entity.get("entity_id")
            synth = f"net:{key}"
            entity["device_id"] = synth
            entity.setdefault("_meta", {}).setdefault("inferred_fields", {})[
                "device_id"
            ] = {
                "join_origin": "network_tracker_enricher",
                "join_confidence": 0.4,
                "field_contract": "synthetic device created for network tracker",
            }
            logging.debug(
                f"network_tracker_enricher created synthetic device: {synth} for {entity.get('entity_id')}"
            )

        return entity
