"""
Area & Floor Enricher: Assigns area_id and floor_id using device and config registries.
- device_id → device_registry.area_id → area_registry.floor_id
- fallback: config_entry_id → config_registry → area/floor
- validates area/floor existence before assignment
- emits provenance in _meta.inferred_fields
"""

import logging

from scripts.enrich.enrichers.base import AbstractEnricher

logger = logging.getLogger(__name__)


def build_device_map(devices):
    return {d["id"]: d for d in devices}


def build_area_map(areas):
    # area registry entries are keyed by 'area_id' in tests and canonical data
    return {a.get("area_id"): a for a in areas}


def build_config_map(config_entries):
    return {c["entry_id"]: c for c in config_entries}


class AreaFloorEnricher(AbstractEnricher):
    def enrich(self, entity: dict, context: dict) -> dict:
        logger.debug(
            f"[DEBUG-ENRICH-START] {entity.get('entity_id')}: sensor_type={entity.get('sensor_type')}, area_id={entity.get('area_id')}, floor_id={entity.get('floor_id')}"
        )
        device_registry = context.get("device_registry", {})
        area_registry = context.get("area_registry", {})
        config_registry = context.get("config_registry", {})
        # Accept both list and dict for registries
        if isinstance(device_registry, list):
            device_registry = build_device_map(device_registry)
        if isinstance(area_registry, list):
            area_registry = build_area_map(area_registry)
        if isinstance(config_registry, list):
            config_registry = build_config_map(config_registry)
        eid = entity.get("entity_id")
        area_id = None
        floor_id = None
        provenance = {
            "join_origin": "area_floor_enricher",
            "join_confidence": 0.8,
            "field_contract": "area/floor inferred via registry",
        }
        # Exemption logic for logic/template/virtual sensors
        if entity.get("sensor_type") in [
            "logic",
            "template",
            "virtual",
        ] and not entity.get("area_id"):
            logger.debug(
                f"[DEBUG-EXEMPTION-BRANCH] {eid}: sensor_type={entity.get('sensor_type')}, initial area_id={entity.get('area_id')}, initial floor_id={entity.get('floor_id')}"
            )
            # Only exempt if area_id is missing/null/empty
            logger.debug(
                f"[DEBUG-EXEMPT-AREA] {eid}: area_id missing, marking as exempted"
            )
            entity["area_id"] = None
            entity.setdefault("_meta", {}).setdefault("inferred_fields", {})[
                "area_id"
            ] = {
                "join_origin": "exemption",
                "join_confidence": 0.0,
                "field_contract": "area_id exempted for logic/template/virtual sensor",
                "exemption_reason": f"area_id not applicable for {entity.get('sensor_type')} sensor",
            }
            # Same logic for floor_id
            if entity.get("floor_id"):
                logger.debug(
                    f"[DEBUG-PROPAGATE-FLOOR] {eid}: Propagating floor_id: {entity.get('floor_id')}"
                )
                entity.setdefault("_meta", {}).setdefault(
                    "inferred_fields", {}
                )["floor_id"] = {
                    "join_origin": "area_floor_enricher",
                    "join_confidence": 0.8,
                    "field_contract": "floor_id inferred via registry",
                }
            else:
                logger.debug(
                    f"[DEBUG-EXEMPT-FLOOR] {eid}: floor_id missing, marking as exempted"
                )
                entity["floor_id"] = None
                entity.setdefault("_meta", {}).setdefault(
                    "inferred_fields", {}
                )["floor_id"] = {
                    "join_origin": "exemption",
                    "join_confidence": 0.0,
                    "field_contract": "floor_id exempted for logic/template/virtual sensor",
                    "exemption_reason": f"floor_id not applicable for {entity.get('sensor_type')} sensor",
                }
            logger.debug(
                f"[DEBUG-EXEMPTION-END] {eid}: area_id={entity.get('area_id')}, floor_id={entity.get('floor_id')}, meta={entity.get('_meta', {}).get('inferred_fields', {})}"
            )
            return entity
        # 1. Try entity_registry > device_registry > heuristic > exemption
        # (entity_registry handled by join_enricher, so here: device_registry)
        device_id = entity.get("device_id")
        if device_id and device_id in device_registry:
            area_id = device_registry[device_id].get("area_id")
            logger.debug(
                f"[DEBUG-DEVICE-REGISTRY] {eid}: device_id={device_id}, area_id from device_registry={area_id}"
            )
        # 2. Try config_entry_id → config_registry → area_id
        if not area_id:
            config_entry_id = entity.get("config_entry_id")
            if config_entry_id and config_entry_id in config_registry:
                area_id = config_registry[config_entry_id].get("area_id")
                logger.debug(
                    f"[DEBUG-CONFIG-REGISTRY] {eid}: config_entry_id={config_entry_id}, area_id from config_registry={area_id}"
                )
        # 3. Validate area_id exists in area_registry
        if area_id and area_id not in area_registry:
            logger.debug(
                f"[DEBUG-AREA-REGISTRY-VALIDATE] {eid}: area_id {area_id} not in area_registry, nulling"
            )
            area_id = None
        # 4. area_id → area_registry.floor_id
        if area_id:
            floor_id = area_registry[area_id].get("floor_id")
            logger.debug(
                f"[DEBUG-FLOOR-LOOKUP] {eid}: area_id={area_id}, floor_id from area_registry={floor_id}"
            )
        # Emit at root
        if area_id:
            entity["area_id"] = area_id
        if floor_id:
            entity["floor_id"] = floor_id
        # Emit in _meta.inferred_fields
        if "_meta" not in entity:
            entity["_meta"] = {}
        if "inferred_fields" not in entity["_meta"]:
            entity["_meta"]["inferred_fields"] = {}
        if area_id:
            entity["_meta"]["inferred_fields"]["area_id"] = provenance.copy()
        if floor_id:
            entity["_meta"]["inferred_fields"]["floor_id"] = provenance.copy()
        logger.debug(
            f"[DEBUG-ENRICH-END] {eid}: area_id={entity.get('area_id')}, floor_id={entity.get('floor_id')}, meta={entity.get('_meta', {}).get('inferred_fields', {})}"
        )
        return entity
