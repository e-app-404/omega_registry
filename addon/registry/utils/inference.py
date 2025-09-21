from typing import Optional, Set, Tuple, Dict
import re
import logging

def infer_area_id(entity: dict, device_map: dict, area_ids: Optional[Set[str]] = None) -> Tuple[str, Dict]:
    """
    Unified area inference logic (inclusive).
    Returns:
        (area_id, trace_dict)
    """
    trace = {"source_fields": [], "method": None, "warnings": []}
    if entity.get('area_id'):
        trace["source_fields"].append("area_id")
        trace["method"] = "entity_area_id"
        return entity['area_id'], trace
    device_id = entity.get('device_id')
    if not device_map:
        trace["warnings"].append("device_map_empty_or_missing")
    if device_id and device_map and device_id not in device_map:
        trace["warnings"].append(f"device_id_not_found:{device_id}")
    if device_id and device_map and device_id in device_map:
        device = device_map[device_id]
        if device.get('area_id'):
            trace["source_fields"].append("device_id")
            trace["method"] = "device_area_id"
            return device['area_id'], trace
        else:
            trace["warnings"].append(f"device_area_id_missing:{device_id}")
    eid = entity.get('entity_id', '')
    slug = eid.split('.')[1] if '.' in eid else ''
    prefix = slug.split('_')[0] if slug else ''
    KNOWN_AREAS = [
        'bedroom', 'kitchen', 'hallway_downstairs', 'hallway_upstairs', 'hallway',
        'ensuite', 'living_room', 'entrance', 'wardrobe', 'desk', 'laundry_room',
        'downstairs', 'upstairs', 'shared', 'private', 'home', 'virtual', 'bamboo',
        'terrazo', 'lucetta', 'brass', 'wall', 'evert', 'psn', 'monstera', 'epad',
        'apple', 'iphone8', 'iphone11', 'iphone14', 'ephone', 'nintendo', 'wallet',
        'keys', 'backpack', 'sonos', 'tp', 'counter', 'network', 'macbook', 'powerstrip',
        'power', 'plant', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday',
        'friday', 'saturday', 'weekday', 'weekend', 'metadata', 'merged', 'room'
    ]
    area_match = None
    # 1. Original regex word-boundary match
    for area in KNOWN_AREAS:
        pattern = re.compile(rf"\\b{re.escape(area)}\\b", re.IGNORECASE)
        if pattern.search(eid) or pattern.search(slug) or pattern.search(prefix):
            area_match = area
            trace["source_fields"].extend(["entity_id", "slug", "prefix"])
            trace["method"] = "prefix_fuzzy_match"
            return area_match, trace
    # 2. Tokenized slug/entity_id fallback match (ENHANCED: n-gram matching)
    slug_tokens = [t.lower() for t in slug.split('_') if t]
    eid_tokens = [t.lower() for t in eid.split('.')[-1].split('_') if t]
    all_tokens = slug_tokens + eid_tokens
    token_match_debug = []
    ngram_attempts = []
    matched_ngram = None
    for n in range(2, len(all_tokens) + 1):
        for i in range(len(all_tokens) - n + 1):
            candidate = "_".join(all_tokens[i:i+n])
            ngram_attempts.append(candidate)
            if candidate in KNOWN_AREAS:
                matched_ngram = candidate
                area_match = candidate
                trace["source_fields"].extend(["slug", "entity_id"])
                trace["method"] = "ngram_token_match|area_fallback_patch"
                trace["area_token_match_debug"] = {
                    "known_area_slugs": KNOWN_AREAS,
                    "slug_tokens": slug_tokens,
                    "entity_id_tokens": eid_tokens,
                    "ngram_attempts": ngram_attempts,
                    "matched_ngram": matched_ngram,
                    "matched_area": candidate
                }
                return area_match, trace
    # 3. Area IDs substring fallback
    if area_ids:
        for area in area_ids:
            if area in eid:
                trace["source_fields"].append("entity_id")
                trace["method"] = "entity_id_substring"
                return area, trace
    # If still unresolved, add debug info for tokenized matching
    trace["area_token_match_debug"] = {
        "known_area_slugs": KNOWN_AREAS,
        "slug_tokens": slug_tokens,
        "entity_id_tokens": eid_tokens,
        "ngram_attempts": ngram_attempts,
        "matched_ngram": matched_ngram,
        "matched_area": None
    }
    # Forced debug print/log for diagnostics
    logging.warning(f"[DEBUG AREA TRACE] entity_id={eid} trace={trace}")
    trace["method"] = "null"
    trace["warnings"].append("no_area_found")
    logging.warning(f"Unresolved area for entity: {eid}")
    return 'null', trace

def patch_devices(devices, area_map):
    enriched = 0
    for dev in devices:
        area_id = dev.get('area_id')
        dev['zone'] = area_id
        room = area_map.get(area_id)
        if room is None or room == '' or room is False:
            room = area_id
        dev['room'] = room
        enriched += 1
    return devices, enriched

def infer_role(entity: dict) -> dict:
    """
    Enhanced role inference utility using auxiliary fields.
    Returns a dict with:
      - role: final inferred role (str or None)
      - confidence: float (0.0-1.0)
      - match_method: str (device_class, original_device_class, translation_key, slug, name, fallback, etc)
      - candidates: dict of all attempted methods and their results
      - role_reason: which field contributed to the semantic_role
      - trace: {source_fields: [...], method: ...}
    """
    from registry.utils.constants import STANDARD_DEVICE_CLASSES, ENTITY_FEATURES
    role = None
    confidence = 0.0
    match_method = None
    candidates = {}
    role_reason = None
    trace = {"source_fields": [], "method": None}
    # 1. Device class or original_device_class
    device_class = entity.get('device_class') or entity.get('original_device_class')
    if device_class and device_class in STANDARD_DEVICE_CLASSES:
        role = device_class
        confidence = 1.0
        match_method = 'device_class/original_device_class'
        candidates['device_class/original_device_class'] = device_class
        role_reason = 'device_class' if entity.get('device_class') else 'original_device_class'
        trace["source_fields"].append(role_reason)
        trace["method"] = match_method
        return {'role': role, 'confidence': confidence, 'match_method': match_method, 'candidates': candidates, 'role_reason': role_reason, 'trace': trace}
    candidates['device_class/original_device_class'] = device_class
    # 2. entity_category
    entity_category = entity.get('entity_category')
    if not role and entity_category:
        role = entity_category
        confidence = 0.8
        match_method = 'entity_category'
        candidates['entity_category'] = entity_category
        role_reason = 'entity_category'
        trace["source_fields"].append('entity_category')
        trace["method"] = match_method
        return {'role': role, 'confidence': confidence, 'match_method': match_method, 'candidates': candidates, 'role_reason': role_reason, 'trace': trace}
    candidates['entity_category'] = entity_category
    # 3. translation_key
    translation_key = entity.get('translation_key')
    if not role and translation_key and translation_key in ENTITY_FEATURES:
        role = translation_key
        confidence = 0.8
        match_method = 'translation_key'
        candidates['translation_key'] = translation_key
        role_reason = 'translation_key'
        trace["source_fields"].append('translation_key')
        trace["method"] = match_method
        return {'role': role, 'confidence': confidence, 'match_method': match_method, 'candidates': candidates, 'role_reason': role_reason, 'trace': trace}
    candidates['translation_key'] = translation_key
    # 4. Slug/domain/name
    eid = entity.get('entity_id', '')
    slug = eid.split('.')[1] if '.' in eid else ''
    domain = eid.split('.')[0] if '.' in eid else ''
    name = (entity.get('friendly_name') or entity.get('name') or '').lower()
    for feature in ENTITY_FEATURES:
        if feature == slug or feature == domain or feature in name:
            role = feature
            confidence = 0.7
            match_method = 'slug/domain/name'
            candidates['slug/domain/name'] = feature
            role_reason = 'slug/domain/name'
            trace["source_fields"].extend(['entity_id', 'friendly_name', 'name'])
            trace["method"] = match_method
            return {'role': role, 'confidence': confidence, 'match_method': match_method, 'candidates': candidates, 'role_reason': role_reason, 'trace': trace}
    candidates['slug/domain/name'] = None
    # 5. Fallback: cluster_role heuristic
    for key in ['device_class', 'original_device_class']:
        if entity.get(key):
            role = entity[key]
            confidence = 0.6
            match_method = key
            candidates[key] = role
            role_reason = key
            trace["source_fields"].append(key)
            trace["method"] = match_method
            return {'role': role, 'confidence': confidence, 'match_method': match_method, 'candidates': candidates, 'role_reason': role_reason, 'trace': trace}
    if entity.get('original_name'):
        role = entity['original_name']
        confidence = 0.5
        match_method = 'original_name'
        candidates['original_name'] = role
        role_reason = 'original_name'
        trace["source_fields"].append('original_name')
        trace["method"] = match_method
        return {'role': role, 'confidence': confidence, 'match_method': match_method, 'candidates': candidates, 'role_reason': role_reason, 'trace': trace}
    for feature in ENTITY_FEATURES:
        if feature in eid:
            role = feature
            confidence = 0.4
            match_method = 'eid_fallback'
            candidates['eid_fallback'] = feature
            role_reason = 'eid_fallback'
            trace["source_fields"].append('entity_id')
            trace["method"] = match_method
            return {'role': role, 'confidence': confidence, 'match_method': match_method, 'candidates': candidates, 'role_reason': role_reason, 'trace': trace}
    # No match
    trace["method"] = None
    return {'role': None, 'confidence': 0.0, 'match_method': None, 'candidates': candidates, 'role_reason': None, 'trace': trace}
