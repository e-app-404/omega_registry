import logging

from scripts.enrich.enrichers.base import AbstractEnricher


# Local utility: is_null_like
def is_null_like(value):
    """Return True if value is semantically null (None, empty string, or 'null')."""
    return value in [None, "", "null"]


class JoinFieldEnricher(AbstractEnricher):
    def __init__(self, join_chains):
        self.join_chains = join_chains
        self.logger = logging.getLogger("join_enricher")

    def enrich(self, entity: dict, context: dict) -> dict:
        lookups = context.get("lookups", {})
        join_stats = context.get("join_stats", {})
        join_blocked = context.get("join_blocked", {})
        context.get("exemptions", set())
        for chain_name, path_chain in self.join_chains.items():
            for step in path_chain:
                if not isinstance(step, (list, tuple)) or len(step) != 3:
                    self.logger.error(
                        f"[JOIN-ERROR] Invalid join chain step in {chain_name}: {step}"
                    )
                    continue
                from_key, source_name, to_key = step
                # Exemption logic: skip enrichment for exempted sensors
                if entity.get("sensor_type") in [
                    "logic",
                    "template",
                    "virtual",
                ] and to_key in ["device_id", "manufacturer", "serial_number"]:
                    entity.setdefault("_meta", {}).setdefault("inferred_fields", {})[
                        to_key
                    ] = {
                        "join_origin": "exemption",
                        "join_confidence": 0.0,
                        "field_contract": f"{to_key} exempted for {entity.get('sensor_type')} sensor",
                        "exemption_reason": f"{to_key} not applicable for {entity.get('sensor_type')} sensor",
                    }
                    entity[to_key] = None
                    continue
                source_dict = lookups.get(source_name, {})
                from_value = entity.get(from_key)
                if from_key not in entity or from_value in [None, "", "null"]:
                    self.logger.info(
                        f"[JOIN-SKIP] {chain_name}: {entity.get('entity_id')} missing {from_key}, join blocked"
                    )
                    join_blocked[(chain_name, from_key)] = (
                        join_blocked.get((chain_name, from_key), 0) + 1
                    )
                    continue
                # Guarded authoritative stamp for area_id
                if to_key == "area_id" and source_name == "core.entity_registry":
                    meta = entity.setdefault("_meta", {}).setdefault(
                        "inferred_fields", {}
                    )
                    prev = meta.get("area_id")
                    prev_conf = prev.get("join_confidence", 0) if prev else 0
                    if (
                        to_key in entity
                        and not is_null_like(entity.get(to_key))
                        and (not prev or prev_conf < 0.8)
                    ):
                        entity[to_key] = entity.get(to_key)
                        meta[to_key] = {
                            "join_origin": "core.entity_registry",
                            "join_confidence": 1.0,
                            "field_contract": "verbatim from entity_registry",
                        }
                        # Provenance merge: record all sources
                        prov = (
                            entity.setdefault("_meta", {})
                            .setdefault("provenance", {})
                            .setdefault("area_id", [])
                        )
                        prov.append(
                            {
                                "enricher": "join_enricher",
                                "origin": "core.entity_registry",
                            }
                        )
                        self.logger.info(
                            f"[JOIN-PROPAGATE] {chain_name}: {entity.get('entity_id')} area_id propagated from core.entity_registry"
                        )
                        join_stats[(chain_name, from_key, to_key, "propagate")] = (
                            join_stats.get(
                                (chain_name, from_key, to_key, "propagate"), 0
                            )
                            + 1
                        )
                        continue
                    else:
                        self.logger.info(
                            f"[JOIN-SKIP] {chain_name}: {entity.get('entity_id')} area_id meta already set with high confidence"
                        )
                        join_stats[(chain_name, from_key, to_key, "skip")] = (
                            join_stats.get((chain_name, from_key, to_key, "skip"), 0)
                            + 1
                        )
                        continue
                if to_key in entity and not is_null_like(entity.get(to_key)):
                    self.logger.info(
                        f"[JOIN-SKIP] {chain_name}: {entity.get('entity_id')} already has {to_key}"
                    )
                    join_stats[(chain_name, from_key, to_key, "skip")] = (
                        join_stats.get((chain_name, from_key, to_key, "skip"), 0) + 1
                    )
                    continue
                source = source_dict.get(entity[from_key])
                if source and to_key in source and not is_null_like(source[to_key]):
                    entity[to_key] = source[to_key]
                    # Emit join_origin and join_confidence at root level
                    entity[f"{to_key}_join_origin"] = source_name or "unknown"
                    entity[f"{to_key}_join_confidence"] = 0.95 if source_name else 0.0
                    # Inject join metadata in _meta
                    entity.setdefault("_meta", {}).setdefault("inferred_fields", {})[
                        to_key
                    ] = {
                        "join_origin": source_name or "unknown",
                        "join_confidence": 0.95 if source_name else 0.0,
                        "field_contract": f"{from_key}->{to_key} via {source_name or 'unknown'}",
                    }
                    # Provenance merge: record all sources
                    prov = (
                        entity.setdefault("_meta", {})
                        .setdefault("provenance", {})
                        .setdefault(to_key, [])
                    )
                    prov.append(
                        {
                            "enricher": "join_enricher",
                            "origin": source_name or "unknown",
                        }
                    )
                    self.logger.info(
                        f"[JOIN] {chain_name}: {entity.get('entity_id')} {from_key}→{to_key}={source[to_key]}"
                    )
                    join_stats[(chain_name, from_key, to_key, "success")] = (
                        join_stats.get((chain_name, from_key, to_key, "success"), 0) + 1
                    )
                else:
                    # If not found, emit exemption if applicable
                    if entity.get("sensor_type") in ["logic", "template", "virtual"]:
                        entity.setdefault("_meta", {}).setdefault(
                            "inferred_fields", {}
                        )[to_key] = {
                            "join_origin": "exemption",
                            "join_confidence": 0.0,
                            "field_contract": f"{to_key} exempted for {entity.get('sensor_type')} sensor",
                            "exemption_reason": f"{to_key} not applicable for {entity.get('sensor_type')} sensor",
                        }
                        entity[to_key] = None
                    self.logger.warning(
                        f"[JOIN-MISS] {chain_name}: {entity.get('entity_id')} {from_key}→{to_key} failed"
                    )
                    join_stats[(chain_name, from_key, to_key, "miss")] = (
                        join_stats.get((chain_name, from_key, to_key, "miss"), 0) + 1
                    )
        return entity
