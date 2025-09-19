import logging


def infer_domain(entity_id):
    """
    Infers the domain from the entity_id, e.g., 'sensor.sun_next_dawn' → 'sensor'.
    Returns None if parsing fails or entity_id is invalid.
    """
    if isinstance(entity_id, str) and "." in entity_id:
        return entity_id.split(".", 1)[0]
    logging.warning(
        f"[DOMAIN-INFER-WARN] Unable to infer domain from malformed entity_id: {entity_id}"
    )
    return None


def infer_device_class(entity):
    """
    Infers the device_class for an entity from attributes, entity_id, or domain using STANDARD_DEVICE_CLASSES.
    Returns (device_class, inference_rule) or (None, None) if not inferrable.
    """
    attrs = entity.get("attributes", {})
    if isinstance(attrs, dict) and "device_class" in attrs:
        return attrs["device_class"], "device_class_from_attributes"
    try:
        from scripts.utils.ha_architecture import STANDARD_DEVICE_CLASSES
    except ImportError:
        logging.warning(
            "[DEVICE-CLASS-INFER-WARN] Could not import STANDARD_DEVICE_CLASSES."
        )
        return None, None
    eid = entity.get("entity_id", "")
    for dc in STANDARD_DEVICE_CLASSES:
        if dc in eid or (isinstance(attrs, dict) and dc in str(attrs.values())):
            return dc, "device_class_from_standard_list"
    return None, None
