def extract_entity_ids_by_platform(registry, platform):
    """
    Extract all entity_ids from a registry (list or dict) with the specified platform.
    Args:
        registry (list or dict): The registry data (list of entities or dict with 'entities' key).
        platform (str): The platform to filter by (e.g., 'smartthings').
    Returns:
        List[str]: List of entity_ids with the given platform.
    """
    # Handle both list-rooted and dict-rooted registries
    if isinstance(registry, dict):
        entities = (
            registry.get("entities")
            or registry.get("data", {}).get("entities")
            or registry.get("data")
            or []
        )
    else:
        entities = registry
    return [
        e["entity_id"]
        for e in entities
        if e.get("platform") == platform and "entity_id" in e
    ]
