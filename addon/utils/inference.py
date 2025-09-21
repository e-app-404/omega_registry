# DEPRECATED — This file has been merged into registry/utils/. Please update references accordingly.

def resolve_area_id(entity, device_map, area_id_set, area_alias_map):
    device_id = entity.get("device_id")
    device = device_map.get(device_id, {})
    area_id = device.get("area_id")
    if area_id in area_id_set:
        return area_id
    # Try alias fallback
    alias = area_alias_map.get(area_id)
    return alias if alias in area_id_set else None

def infer_role(entity, rules):
    device_class = entity.get("device_class", "")
    domain = entity.get("platform", "")
    for rule in rules:
        if rule["device_class"] == device_class and rule["domain"] == domain:
            return rule["role"]
    return "unknown"

def compute_status(disabled_by, hidden_by):
    if disabled_by:
        return "disabled"
    if hidden_by:
        return "hidden"
    return "active"
