import fnmatch
import logging
import re


def normalize_platforms(tier_definitions):
    for tier in tier_definitions.values():
        match = tier.get("match", {})
        if "platforms" in match:
            match["platforms"] = [p.lower() for p in match["platforms"]]


def tier_classification(entity, tier_definitions, fallback_tier=None):
    """
    Canonical, contract-compliant tier classification.
    α: platform in α list, entity_category is None or 'None', platform not in template/group/aggregation. device_id optional.
    All other tiers: iterate and match as before.
    """
    normalize_platforms(tier_definitions)
    entity_id = entity.get("entity_id")
    domain = (entity.get("domain") or "").lower() if entity.get("domain") else None
    platform = (entity.get("platform") or "").lower()
    device_id = entity.get("device_id")
    entity_category = entity.get("entity_category")
    file_path = entity.get("file_path")
    attributes_dict = entity.get("attributes", {})
    upstream_sources = entity.get("upstream_sources", [])

    def has_attr(attr):
        return attr in entity or attr in attributes_dict

    def log_match(tier_name, trigger):
        logging.info(f"[TIER] {entity_id} → {tier_name} (matched: {trigger})")

    # --- α: canonical logic ---
    alpha = tier_definitions.get("α", {})
    alpha_rules = alpha.get("match", {})
    alpha_platforms = set(alpha_rules.get("platforms", []))
    alpha_entity_category = alpha_rules.get("entity_category", [])
    if (
        platform in alpha_platforms
        and (
            entity_category in alpha_entity_category
            or (entity_category is None and None in alpha_entity_category)
        )
        and platform not in ("template", "group", "sensor aggregation")
    ):
        log_match("α", "canonical α")
        return "α", "canonical α"
    # --- all other tiers: iterate and match as before ---
    for tier_name, tier in tier_definitions.items():
        if tier_name == "α":
            continue
        rules = tier.get("match", {})
        # 1. entity_ids (exact)
        for eid in rules.get("entity_ids", []):
            if entity_id == eid:
                log_match(tier_name, f"entity_id:{eid}")
                return tier_name, f"entity_id:{eid}"
        # 2. platforms (list, case-insensitive)
        if "platforms" in rules and platform in rules["platforms"]:
            log_match(tier_name, f"platform:{platform}")
            return tier_name, f"platform:{platform}"
        # 3. domains (list, case-insensitive)
        if (
            "domains" in rules
            and domain
            and domain in [d.lower() for d in rules["domains"]]
        ):
            log_match(tier_name, f"domain:{domain}")
            return tier_name, f"domain:{domain}"
        # 4. entity_category (list)
        if "entity_category" in rules and (
            entity_category in rules["entity_category"]
            or (entity_category is None and None in rules["entity_category"])
        ):
            log_match(tier_name, f"entity_category:{entity_category}")
            return tier_name, f"entity_category:{entity_category}"
        # 5. device_id (regex)
        if "device_id" in rules:
            if device_id and re.fullmatch(rules["device_id"], device_id):
                log_match(tier_name, f"device_id:{device_id}")
                return tier_name, f"device_id:{device_id}"
        # 6. references_entities (bool)
        if rules.get("references_entities"):
            all_attr_vals = list(attributes_dict.values()) + [
                entity.get(k) for k in entity if k != "attributes"
            ]
            if any(isinstance(v, str) and "." in v for v in all_attr_vals if v):
                log_match(tier_name, "references_entities")
                return tier_name, "references_entities"
        # 7. entity_id_patterns (list, regex)
        for pattern in rules.get("entity_id_patterns", []):
            if entity_id and re.fullmatch(pattern, entity_id):
                log_match(tier_name, f"entity_id_pattern:{pattern}")
                return tier_name, f"entity_id_pattern:{pattern}"
        # 8. attributes_include (list, search both top-level and attributes)
        if "attributes_include" in rules:
            if all(has_attr(attr) for attr in rules["attributes_include"]):
                log_match(
                    tier_name, f"attributes_include:{rules['attributes_include']}"
                )
                return tier_name, f"attributes_include:{rules['attributes_include']}"
        # 9. file_path_patterns (list, glob)
        for pattern in rules.get("file_path_patterns", []):
            if file_path and fnmatch.fnmatch(file_path, pattern):
                log_match(tier_name, f"file_path_pattern:{pattern}")
                return tier_name, f"file_path_pattern:{pattern}"
        # 10. upstream_sources_count (string, e.g. '>1')
        if "upstream_sources_count" in rules and upstream_sources is not None:
            try:
                count = len(upstream_sources)
                expr = rules["upstream_sources_count"]
                if expr.startswith(">") and count > int(expr[1:]):
                    log_match(tier_name, f"upstream_sources_count:{expr}")
                    return tier_name, f"upstream_sources_count:{expr}"
                elif expr.startswith("<") and count < int(expr[1:]):
                    log_match(tier_name, f"upstream_sources_count:{expr}")
                    return tier_name, f"upstream_sources_count:{expr}"
                elif expr.isdigit() and count == int(expr):
                    log_match(tier_name, f"upstream_sources_count:{expr}")
                    return tier_name, f"upstream_sources_count:{expr}"
            except Exception:
                pass
    # --- fallback ---
    if fallback_tier is not None:
        logging.info(f"[TIER] {entity_id} → {fallback_tier} (fallback)")
        return fallback_tier, "fallback"
    logging.warning(
        f"[TIER-DEBUG] entity_id: {entity_id}, fields: {entity}, reason: no matching rule"
    )
    return None, "No tier match"


# Example usage (for test harness):
# tier, origin = tier_classification(entity, tier_definitions)
# if tier:
#     print(f"[TIER] {entity['entity_id']} assigned to {tier} via {origin}")
# else:
#     print(f"[TIER-MISS] {entity['entity_id']} not classified: {origin}")
