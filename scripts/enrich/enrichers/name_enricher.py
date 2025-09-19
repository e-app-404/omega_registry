"""
Name Enricher: Standardizes entity naming with a single authoritative resolved_name field.
- Priority: name > original_name > entity_id fallback
- Emits provenance in _meta.inferred_fields.resolved_name
"""

from scripts.enrich.enrichers.base import AbstractEnricher


class NameEnricher(AbstractEnricher):
    def enrich(self, entity: dict, context: dict) -> dict:
        entity.setdefault("_meta", {}).setdefault("inferred_fields", {})
        # Exemption logic for logic/template/virtual sensors
        if entity.get("sensor_type") in ["logic", "template", "virtual"]:
            entity["resolved_name"] = None
            entity["_meta"]["inferred_fields"]["resolved_name"] = {
                "join_origin": "exemption",
                "join_confidence": 0.0,
                "field_contract": "resolved_name exempted for logic/template/virtual sensor",
                "exemption_reason": f"resolved_name not applicable for {entity.get('sensor_type')} sensor",
            }
            return entity
        if "name" in entity and entity["name"]:
            entity["resolved_name"] = entity["name"]
            entity["_meta"]["inferred_fields"]["resolved_name"] = {
                "join_origin": "name",
                "join_confidence": 1.0,
                "field_contract": "resolved_name from name",
            }
        elif "original_name" in entity and entity["original_name"]:
            entity["resolved_name"] = entity["original_name"]
            entity["_meta"]["inferred_fields"]["resolved_name"] = {
                "join_origin": "original_name",
                "join_confidence": 0.95,
                "field_contract": "resolved_name from original_name",
            }
        else:
            raw_id = entity.get("entity_id", "unnamed_entity")
            fallback = raw_id.replace("_", " ").replace(".", " ").title()
            entity["resolved_name"] = fallback
            entity["_meta"]["inferred_fields"]["resolved_name"] = {
                "join_origin": "entity_id fallback",
                "join_confidence": 0.75,
                "field_contract": "resolved_name fallback from entity_id",
            }
        return entity
