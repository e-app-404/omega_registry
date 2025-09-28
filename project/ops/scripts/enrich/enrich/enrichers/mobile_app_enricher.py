import logging


class MobileAppEnricher:
    """Lightweight enricher for mobile_app entities.

    Behavior:
    - Inspect attributes for device identifiers (device_id, app_instance_id, id)
    - Attempt to match against existing device registry (context['device_registry'] expected)
    - If a match is found, attach device_id; otherwise optionally create a synthetic device id
    """

    def __init__(self, create_synthetic=False):
        self.create_synthetic = create_synthetic

    def enrich(self, entity, context):
        if entity.get("platform") != "mobile_app":
            return entity

        attrs = entity.get("attributes", {}) or {}
        # common attribute keys where a mobile app might expose an id
        candidate_keys = [
            "device_id",
            "device",
            "app_instance_id",
            "id",
            "instance_id",
        ]
        candidate = None
        for k in candidate_keys:
            if k in attrs and attrs[k]:
                candidate = attrs[k]
                break

        # Try to match an existing device by identifier in context
        devmap = {}
        if candidate and "device_registry" in context:
            raw = context["device_registry"]
            # normalize device registry into a mapping of device_id->device_obj
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
                ids = dev.get("identifiers") or []
                # identifiers may be a list of tuples or strings
                if candidate in ids or any(candidate == str(x) for x in ids):
                    entity["device_id"] = did
                    entity.setdefault("_meta", {}).setdefault("inferred_fields", {})[
                        "device_id"
                    ] = {
                        "join_origin": "mobile_app_enricher",
                        "join_confidence": 0.9,
                        "field_contract": "matched by app instance identifier",
                    }
                    return entity

        # No match found — optionally create a synthetic device id
        if self.create_synthetic:
            # create deterministic synthetic id
            owner = (
                attrs.get("owner")
                or attrs.get("user")
                or entity.get("entity_id").split(".")[0]
            )
            synth = f"mobile_app:{owner}"
            entity["device_id"] = synth
            entity.setdefault("_meta", {}).setdefault("inferred_fields", {})[
                "device_id"
            ] = {
                "join_origin": "mobile_app_enricher",
                "join_confidence": 0.4,
                "field_contract": "synthetic device created for mobile_app",
            }
            logging.debug(
                f"mobile_app_enricher created synthetic device: {synth} for {entity.get('entity_id')}"
            )

        return entity
