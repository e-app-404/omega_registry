from typing import Optional, Set
from registry.utils.inference import infer_area_id

def make_cluster_id(area_id: Optional[str], role: Optional[str]) -> Optional[str]:
    """
    Centralized cluster_id construction for all registry scripts.
    - area_id: Area slug or None
    - role: Role string (required)
    Returns: cluster_id as "{area_id or 'null'}_{role}" or None if role is missing.
    """
    if not role:
        return None
    return f"{area_id or 'null'}_{role}"

def build_device_map(device_registry: dict) -> dict:
    """
    Centralized device_map construction for all registry scripts.
    Accepts a device registry dict and returns {device_id: device_dict}.
    """
    return {d['id']: d for d in device_registry.get('data', {}).get('devices', [])}

def get_device_area(device_id: str, device_map: dict) -> Optional[str]:
    """
    Returns the area_id for a given device_id from the device_map, or None if not found.
    """
    device = device_map.get(device_id)
    if device:
        return device.get('area_id')
    return None

def resolve_cluster_metadata(entity: dict, device_map: dict, area_ids: Set[str]) -> dict:
    """
    Centralized resolver for cluster/entity metadata extraction.
    Returns a dict with standardized fields:
      - entity_id
      - area_id (inferred or enriched)
      - cluster_role (from entity or device)
      - cluster_id (centralized construction)
      - platform (from entity)
      - device_id (from entity)
    """
    # Prefer existing enriched fields from input
    area_id = entity.get("final_area") or entity.get("area_id")
    role = entity.get("role")
    if area_id and role:
        # Optional: debug log for a few sample entities
        if entity.get("entity_id", "").startswith("sensor.merged_bedroom") or entity.get("entity_id", "").startswith("binary_sensor.hallway_downstairs"):
            print(f"[DEBUG] resolve_cluster_metadata: entity_id={entity.get('entity_id')}, area_id={area_id}, role={role}, cluster_id={area_id}_{role}")
        return {
            "entity_id": entity.get("entity_id"),
            "area_id": area_id,
            "cluster_role": role,
            "cluster_id": f"{area_id}_{role}",
            "platform": entity.get("platform"),
            "device_id": entity.get("device_id"),
        }
    # Fallback to legacy inference if enriched fields are missing
    entity_id = entity.get('entity_id')
    device_id = entity.get('device_id')
    area_id_result = infer_area_id(entity, device_map, area_ids)
    area_id = area_id_result[0] if isinstance(area_id_result, tuple) else area_id_result
    # Try to infer cluster_role from entity, fallback to device if present
    cluster_role = entity.get('cluster_role')
    if not cluster_role and device_id and device_id in device_map:
        cluster_role = device_map[device_id].get('cluster_role')
    cluster_id = make_cluster_id(area_id, cluster_role)
    platform = entity.get('platform')
    return {
        'entity_id': entity_id,
        'area_id': area_id,
        'cluster_role': cluster_role,
        'cluster_id': cluster_id,
        'platform': platform,
        'device_id': device_id,
    }
