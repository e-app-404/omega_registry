def extract_data(file_path: str, content) -> list:
    import logging
    # PATCH: Handle both dict and list top-level structures
    if isinstance(content, list):
        print(f"[INFO] Top-level list detected in {file_path}, returning as entries.")
        if content and all(isinstance(e, dict) for e in content):
            print(f"[INFO] Extracted {len(content)} entries from: {file_path}")
            return content
        else:
            print(f"[WARN] Top-level list in {file_path} is not a list of dicts.")
            return []
    if not isinstance(content, dict):
        print(f"[WARN] Unexpected top-level type in {file_path}: {type(content)}")
        return []
    # Explicit handlers for patch targets
    if file_path.endswith('counter'):
        # PATCH: counter uses 'items' under 'data'
        entries = content.get("data", {}).get("items", [])
    elif file_path.endswith('trace.saved_traces') or "trace" in file_path:
        # PATCH: trace.saved_traces uses dict of lists under 'data'
        entries = []
        for v in content.get("data", {}).values():
            if isinstance(v, list):
                entries.extend(v)
    elif file_path.endswith('person'):
        # PATCH: person uses 'items' under 'data'
        entries = content.get("data", {}).get("items", [])
    elif file_path.endswith('input_boolean'):
        entries = content.get("data", {}).get("items", [])
    elif file_path.endswith('input_datetime'):
        entries = content.get("data", {}).get("items", [])
    elif file_path.endswith('input_datetime.verified.generated.json'):
        entries = content.get("data", {}).get("items", [])
    elif file_path.endswith('input_number.verified.generated.json'):
        entries = content.get("data", {}).get("items", [])
    elif file_path.endswith('input_text.verified.generated.json'):
        entries = content.get("data", {}).get("items", [])
    # Fallback for .verified.generated.json files by prefix
    elif file_path.endswith('.verified.generated.json'):
        if file_path.startswith('input_number'):
            entries = content.get("data", {}).get("items", [])
        elif file_path.startswith('input_text'):
            entries = content.get("data", {}).get("items", [])
        elif file_path.startswith('input_datetime'):
            entries = content.get("data", {}).get("items", [])
        else:
            entries = []
    # Existing handlers
    elif "entity_registry" in file_path:
        entries = content.get("data", {}).get("entities", [])
    elif "device_registry" in file_path:
        entries = content.get("data", {}).get("devices", [])
    elif "area_registry" in file_path:
        entries = content.get("data", {}).get("areas", [])
    elif "floor_registry" in file_path:
        entries = content.get("data", {}).get("floors", [])
    elif "config_entries" in file_path:
        entries = content.get("data", {}).get("entries", [])
    elif "label_registry" in file_path:
        entries = content.get("data", {}).get("labels", [])
    elif "category_registry" in file_path:
        # PATCH: category_registry uses dict of lists under 'categories'
        entries = []
        for v in content.get("data", {}).get("categories", {}).values():
            if isinstance(v, list):
                entries.extend(v)
    elif "restore_state" in file_path:
        entries = content.get("data", [])
    elif "exposed_entities" in file_path:
        entries = list(content.get("data", {}).get("exposed_entities", {}).keys())
    else:
        entries = []
    # Log extraction outcome
    if entries and isinstance(entries, list) and len(entries) > 0:
        print(f"[INFO] Extracted {len(entries)} entries from: {file_path}")
    else:
        print(f"[WARN] No valid entries extracted from: {file_path}")
    return entries
