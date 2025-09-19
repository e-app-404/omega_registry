from scripts.enrich.enrichers.base import AbstractEnricher


def build_device_map(devices):
    return {d["id"]: d for d in devices}


def build_config_map(config_entries):
    return {c["entry_id"]: c for c in config_entries}


class ConfigEntryEnricher(AbstractEnricher):
    def enrich(self, entity: dict, context: dict) -> dict:
        device_registry = context.get("device_registry", {})
        config_registry = context.get("config_registry", {})
        # Accept both list and dict for device_registry/config_registry
        if isinstance(device_registry, list):
            device_registry = build_device_map(device_registry)
        if isinstance(config_registry, list):
            config_registry = build_config_map(config_registry)
        device_id = entity.get("device_id")
        integrations = []
        multi_integration = False
        if device_id and device_id in device_registry:
            device = device_registry[device_id]
            config_entries_list = device.get("config_entries", [])
            multi_integration = len(config_entries_list) > 1
            for entry_id in config_entries_list:
                cfg = config_registry.get(entry_id)
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
                    "integration_domain": entity.get("platform"),
                    "integration_entry_id": None,
                    "integration_title": None,
                    "integration_source": None,
                    "discovery_keys": None,
                    "integration_unique_id": None,
                    "integration_url": None,
                }
            )
        entity["enriched_integrations"] = integrations
        entity["multi_integration"] = multi_integration
        return entity
