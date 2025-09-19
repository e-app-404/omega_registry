from scripts.enrich.enrichers.base import AbstractEnricher


def build_device_map(devices):
    return {d["id"]: d for d in devices}


def extract_mac(connections):
    if not isinstance(connections, list):
        return None
    for conn in connections:
        if isinstance(conn, (list, tuple)) and len(conn) == 2 and conn[0] == "mac":
            return conn[1].lower()
    return None


class DeviceRegistryEnricher(AbstractEnricher):
    def enrich(self, entity: dict, context: dict) -> dict:
        device_registry = context.get("device_registry", {})
        # Accept both list and dict for device_registry
        if isinstance(device_registry, list):
            device_registry = build_device_map(device_registry)
        dev_id = entity.get("device_id")
        device = device_registry.get(dev_id)
        context.setdefault(
            "serial_number_missing_count", 0
        )
        if device:
            # MAC
            mac = extract_mac(device.get("connections", []))
            if mac:
                entity["mac"] = mac
                entity.setdefault("field_inheritance", {})["mac"] = "device_registry"
            # via_device_id
            via = device.get("via_device_id")
            if via is not None:
                entity["via_device_id"] = via
                entity.setdefault("field_inheritance", {})[
                    "via_device_id"
                ] = "device_registry"
            # serial_number
            serial = device.get("serial_number") if "serial_number" in device else None
            if serial is not None:
                entity["serial_number"] = serial
                entity.setdefault("field_inheritance", {})[
                    "serial_number"
                ] = "device_registry"
                entity.setdefault("_meta", {}).setdefault("inferred_fields", {})[
                    "serial_number"
                ] = {
                    "join_origin": "device_registry",
                    "join_confidence": 0.95,
                    "field_contract": "serial_number from device_registry",
                }
            else:
                import logging

                logging.warning(
                    f"Serial number missing in device for device_id={dev_id}"
                )
                context["serial_number_missing_count"] += 1
            # manufacturer
            entity["manufacturer"] = device.get("manufacturer")
            # device_name
            name_by_user = device.get("name_by_user")
            name = device.get("name")
            entity["device_name"] = (
                name_by_user if name_by_user not in [None, "", "null"] else name
            )
            # primary_config_entry
            entity["primary_config_entry"] = device.get("primary_config_entry")
            # identifiers
            entity["identifiers"] = device.get("identifiers")
        return entity
