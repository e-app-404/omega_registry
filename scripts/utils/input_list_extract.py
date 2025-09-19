def extract_data(file_path: str, content) -> list:
    """
    PATCH-REGISTRY-FORMAT-VALIDATION-V1
    Supported registry formats:
    1. Top-level list of dicts:
       [ { ... }, { ... } ]
    2. Dict with 'data' field containing a list under a known key:
       { "data": { "devices": [ ... ] } }
       { "data": { "entities": [ ... ] } }
       { "data": { "areas": [ ... ] } }
       { "data": { "items": [ ... ] } }
    3. Dict with 'flatmap' key containing a list:
       { "flatmap": [ ... ] }
    Validation logic:
    - Warn if top-level type is not list or dict.
    - Warn if list contains non-dict entries.
    - Warn if dict missing expected keys.
    - Warn if extracted entries are empty.
    """
    # PATCH: Handle both dict and list top-level structures
    if isinstance(content, list):
        print(f"[INFO] Top-level list detected in {file_path}, returning as entries.")
        if content and all(isinstance(e, dict) for e in content):
            print(f"[INFO] Extracted {len(content)} entries from: {file_path}")
            return content
        else:
            print(
                f"[ERROR] Top-level list in {file_path} contains non-dict entries. Format should be a list of dicts."
            )
            return []
    if not isinstance(content, dict):
        print(
            f"[ERROR] Unexpected top-level type in {file_path}: {type(content)}. Expected dict or list."
        )
        return []
    # PATCH: Support for flatmap schema
    if "flatmap" in content and isinstance(content["flatmap"], list):
        print(f"[INFO] 'flatmap' key detected in {file_path}, returning as entries.")
        return content["flatmap"]
    # Explicit handlers for patch targets
    entries = []
    if file_path.endswith("counter"):
        entries = content.get("data", {}).get("items", [])
        if "items" not in content.get("data", {}):
            print(f"[ERROR] 'items' key missing in 'data' for {file_path}.")
    elif file_path.endswith("trace.saved_traces") or "trace" in file_path:
        for v in content.get("data", {}).values():
            if isinstance(v, list):
                entries.extend(v)
        if not entries:
            print(
                f"[ERROR] No list values found in 'data' for {file_path} (trace handler)."
            )
    elif file_path.endswith("person"):
        entries = content.get("data", {}).get("items", [])
        if "items" not in content.get("data", {}):
            print(f"[ERROR] 'items' key missing in 'data' for {file_path}.")
    elif file_path.endswith("input_boolean"):
        entries = content.get("data", {}).get("items", [])
        if "items" not in content.get("data", {}):
            print(f"[ERROR] 'items' key missing in 'data' for {file_path}.")
    elif file_path.endswith("input_number"):
        entries = content.get("data", {}).get("items", [])
        if "items" not in content.get("data", {}):
            print(f"[ERROR] 'items' key missing in 'data' for {file_path}.")
    elif file_path.endswith("input_text"):
        entries = content.get("data", {}).get("items", [])
        if "items" not in content.get("data", {}):
            print(f"[ERROR] 'items' key missing in 'data' for {file_path}.")
    elif file_path.endswith("input_datetime"):
        entries = content.get("data", {}).get("items", [])
        if "items" not in content.get("data", {}):
            print(f"[ERROR] 'items' key missing in 'data' for {file_path}.")
    elif file_path.endswith("input_datetime.verified.generated.json"):
        entries = content.get("data", {}).get("items", [])
        if "items" not in content.get("data", {}):
            print(f"[ERROR] 'items' key missing in 'data' for {file_path}.")
    elif file_path.endswith("input_number.verified.generated.json"):
        entries = content.get("data", {}).get("items", [])
        if "items" not in content.get("data", {}):
            print(f"[ERROR] 'items' key missing in 'data' for {file_path}.")
    elif file_path.endswith("input_text.verified.generated.json"):
        entries = content.get("data", {}).get("items", [])
        if "items" not in content.get("data", {}):
            print(f"[ERROR] 'items' key missing in 'data' for {file_path}.")
    # Fallback for .verified.generated.json files by prefix
    elif file_path.endswith(".verified.generated.json"):
        if file_path.startswith("input_number"):
            entries = content.get("data", {}).get("items", [])
            if "items" not in content.get("data", {}):
                print(f"[ERROR] 'items' key missing in 'data' for {file_path}.")
        elif file_path.startswith("input_text"):
            entries = content.get("data", {}).get("items", [])
            if "items" not in content.get("data", {}):
                print(f"[ERROR] 'items' key missing in 'data' for {file_path}.")
        elif file_path.startswith("input_datetime"):
            entries = content.get("data", {}).get("items", [])
            if "items" not in content.get("data", {}):
                print(f"[ERROR] 'items' key missing in 'data' for {file_path}.")
        else:
            print(f"[ERROR] Unknown .verified.generated.json prefix for {file_path}.")
            entries = []
    # Existing handlers
    elif "entity_registry" in file_path:
        entries = content.get("data", {}).get("entities", [])
        if "entities" not in content.get("data", {}):
            print(f"[ERROR] 'entities' key missing in 'data' for {file_path}.")
    elif "device_registry" in file_path:
        entries = content.get("data", {}).get("devices", [])
        if "devices" not in content.get("data", {}):
            print(f"[ERROR] 'devices' key missing in 'data' for {file_path}.")
    elif "area_registry" in file_path:
        entries = content.get("data", {}).get("areas", [])
        if "areas" not in content.get("data", {}):
            print(f"[ERROR] 'areas' key missing in 'data' for {file_path}.")
    elif "floor_registry" in file_path:
        entries = content.get("data", {}).get("floors", [])
        if "floors" not in content.get("data", {}):
            print(f"[ERROR] 'floors' key missing in 'data' for {file_path}.")
    elif "config_entries" in file_path:
        entries = content.get("data", {}).get("entries", [])
        if "entries" not in content.get("data", {}):
            print(f"[ERROR] 'entries' key missing in 'data' for {file_path}.")
    elif "label_registry" in file_path:
        entries = content.get("data", {}).get("labels", [])
        if "labels" not in content.get("data", {}):
            print(f"[ERROR] 'labels' key missing in 'data' for {file_path}.")
    elif "category_registry" in file_path:
        entries = []
        for v in content.get("data", {}).get("categories", {}).values():
            if isinstance(v, list):
                entries.extend(v)
        if not entries:
            print(f"[ERROR] No list values found in 'categories' for {file_path}.")
    elif "restore_state" in file_path:
        entries = content.get("data", [])
        if not entries:
            print(
                f"[ERROR] No entries found in 'data' for {file_path} (restore_state handler)."
            )
    elif "exposed_entities" in file_path:
        entries = list(content.get("data", {}).get("exposed_entities", {}).keys())
        if not entries:
            print(f"[ERROR] No exposed_entities found in 'data' for {file_path}.")
    else:
        print(f"[ERROR] No handler for file type: {file_path}. Returning empty list.")
        entries = []
    # Log extraction outcome
    if entries and isinstance(entries, list) and len(entries) > 0:
        print(f"[INFO] Extracted {len(entries)} entries from: {file_path}")
    else:
        print(
            f"[ERROR] No valid entries extracted from: {file_path}. Check format and keys."
        )
    return entries


# PATCH-REGISTRY-FORMAT-VALIDATION-V1 END
