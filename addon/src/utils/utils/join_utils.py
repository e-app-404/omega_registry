def get_device(device_id, device_by_id):
    if device_id:
        return device_by_id.get(device_id)
    return None


def get_area(area_id, area_by_id):
    if area_id:
        return area_by_id.get(area_id)
    return None


def get_floor(floor_id, floor_by_id):
    if floor_id:
        return floor_by_id.get(floor_id)
    return None


def get_config(entry_id, config_by_entry):
    if entry_id:
        return config_by_entry.get(entry_id)
    return None


def get_restore(entity_id, restore_by_entity):
    if entity_id:
        return restore_by_entity.get(entity_id)
    return None


def is_exposed(entity_id, exposed_set):
    return entity_id in exposed_set


def get_label(label_id, label_by_id):
    if label_id:
        return label_by_id.get(label_id)
    return None


def get_category(category_id, category_by_id):
    if category_id:
        return category_by_id.get(category_id)
    return None


def get_person(person_id, person_by_id):
    if person_id:
        return person_by_id.get(person_id)
    return None


def get_input_boolean(input_boolean_id, input_boolean_by_id):
    if input_boolean_id:
        return input_boolean_by_id.get(input_boolean_id)
    return None


def get_input_datetime(input_datetime_id, input_datetime_by_id):
    if input_datetime_id:
        return input_datetime_by_id.get(input_datetime_id)
    return None


def get_input_number(input_number_id, input_number_by_id):
    if input_number_id:
        return input_number_by_id.get(input_number_id)
    return None


def get_input_text(input_text_id, input_text_by_id):
    if input_text_id:
        return input_text_by_id.get(input_text_id)
    return None


def get_counter(counter_id, counter_by_id):
    if counter_id:
        return counter_by_id.get(counter_id)
    return None


def get_trace(trace_id, trace_by_id):
    if trace_id:
        return trace_by_id.get(trace_id)
    return None


def extract_connection_fields(device):
    """
    Extracts known identifier types (mac, upnp, etc.) from device['connections'] and sets them as top-level fields.
    Returns the device dict with new fields if found.
    """
    if not device or "connections" not in device:
        return device
    for conn in device.get("connections", []):
        if isinstance(conn, (list, tuple)) and len(conn) == 2:
            if conn[0] == "mac":
                device["mac"] = conn[1]
            elif conn[0] == "upnp":
                device["upnp_id"] = conn[1]
            # Extend here for other identifier types as needed
    return device


import json
from datetime import datetime

authority_tiers = {"canonical": 1, "enrichment": 2, "manual": 3, "observational": 4}


def resolve_conflict(
    field, candidates, entity_id=None, log_path=None, contract_rules=None
):
    """
    Resolve field-level conflicts using authority tiers and override flags, now contract-driven.
    candidates: list of dicts, each with keys: value, source, tier, override (optional)
    contract_rules: dict with keys 'authority_order' (list), 'override_rules' (dict)
    Returns: winner value, winner source, log entry (if conflict)
    """

    # Use contract-driven authority order if provided
    def tier_rank(tier):
        if contract_rules and "authority_order" in contract_rules:
            authority_order = contract_rules["authority_order"]
            try:
                return authority_order.index(tier)
            except Exception:
                return 99
        else:
            return authority_tiers.get(tier, 99)

    # Sort candidates by authority order
    sorted_candidates = sorted(candidates, key=lambda c: tier_rank(c["tier"]))
    winner = sorted_candidates[0]
    overridden = sorted_candidates[1:]
    reason = None
    # Contract-driven override rules
    if contract_rules and "override_rules" in contract_rules:
        for cand in overridden:
            rule = contract_rules["override_rules"].get(field, {})
            if (
                rule.get("allow_override", False)
                and cand.get("override", False)
                and cand["value"] not in [None, "", [], {}]
            ):
                winner = cand
                reason = f"Override by contract rule in lower tier ({cand['tier']})"
                break
    # If winner value is null/unknown, check for override in lower tier
    if winner["value"] in [None, "", [], {}]:
        for cand in overridden:
            if cand.get("override", False) and cand["value"] not in [None, "", [], {}]:
                winner = cand
                reason = f"Override flag present in lower tier ({cand['tier']})"
                break
    # If not overridden, preserve null from higher
    if not reason and winner["value"] in [None, "", [], {}]:
        reason = "Null/unknown in higher tier, no valid override"
    # Log conflict if more than one candidate
    if len(candidates) > 1 and log_path:
        log_entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "entity_id": entity_id,
            "field": field,
            "candidates": candidates,
            "source_winner": winner["source"],
            "winner_tier": winner["tier"],
            "overridden_sources": [c["source"] for c in overridden],
            "reason": reason or "Higher authority tier wins",
            "contract_rules": contract_rules,
        }
        with open(log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    return winner["value"], winner["source"], reason
