import json
import sys
import os
import datetime

def main():
    if len(sys.argv) != 3:
        print("Usage: python scripts/diagnose_device_without_area.py <input_alpha_sensor_registry.json> <core.device_registry.json>")
        sys.exit(1)
    input_path = sys.argv[1]
    device_registry_path = sys.argv[2]

    with open(input_path, 'r') as f:
        clusters = json.load(f)
    with open(device_registry_path, 'r') as f:
        device_registry = json.load(f)

    # Build device_id -> area_id map
    device_area_map = {}
    for device in device_registry.get('data', {}).get('devices', []):
        device_id = device.get('id')
        area_id = device.get('area_id')
        if device_id:
            device_area_map[device_id] = area_id

    results = []
    for cluster in clusters:
        entity_ids = cluster.get('entity_ids', [])
        device_ids = list(set(cluster.get('device_ids', [])))
        missing_area_device_ids = []
        for device_id in device_ids:
            area_id = device_area_map.get(device_id)
            if area_id is None:
                missing_area_device_ids.append(device_id)
        if device_ids and missing_area_device_ids:
            results.append({
                "cluster_id": cluster.get('cluster_id'),
                "entity_ids": entity_ids,
                "device_ids": device_ids,
                "missing_area_device_ids": missing_area_device_ids,
                "reason": "Device exists but has no mapped area_id"
            })

    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join(os.path.dirname(__file__), '../data')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"clusters_with_device_but_missing_area.{timestamp}.json")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Diagnostics written to {output_path}")
    # Append to copilot_patchlog_overview.log
    log_path = os.path.join(os.path.dirname(__file__), '../copilot_patchlog_overview.log')
    with open(log_path, 'a') as logf:
        logf.write(f"[DIAGNOSE-DEVICE-WITHOUT-AREA] {len(results)} clusters found, output: {output_path}\n")

if __name__ == "__main__":
    main()
