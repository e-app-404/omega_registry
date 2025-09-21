import json
import sys
import os
import datetime

# Usage: python scripts/emit_advanced_unresolved_cluster_diagnostics.py <input_alpha_sensor_registry.json> <output_diagnostics.json>
def main():
    if len(sys.argv) != 3:
        print("Usage: python scripts/emit_advanced_unresolved_cluster_diagnostics.py <input_alpha_sensor_registry.json> <output_diagnostics.json>")
        sys.exit(1)
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    with open(input_path, 'r') as f:
        clusters = json.load(f)
    diagnostics = []
    for cluster in clusters:
        failed_steps = []
        reasons = {}
        # Area diagnostic
        if cluster.get('final_area', None) == 'unknown_area':
            failed_steps.append('area')
            if not cluster.get('entity_ids'):
                reasons['area'] = 'No entity_ids present.'
            else:
                # Heuristic: check for device_id, location, or area hints
                entity_ids = cluster['entity_ids']
                if all('.' not in eid for eid in entity_ids):
                    reasons['area'] = 'Entity_id format unrecognized.'
                elif any('mobile_app' in eid or 'systemmonitor' in eid or 'ambient_network' in eid for eid in entity_ids):
                    reasons['area'] = 'Entity domain is mobile_app/systemmonitor/ambient_network (not mapped to area).'
                else:
                    reasons['area'] = 'No device_id or area mapping found for entity.'
        # Role diagnostic
        if cluster.get('role', None) in ('unclassified', 'diagnostic', None, ''):
            failed_steps.append('role')
            if not cluster.get('entity_ids'):
                reasons['role'] = 'No entity_ids present.'
            else:
                # Heuristic: check for domain/class
                entity_ids = cluster['entity_ids']
                if any(eid.startswith('sensor.') for eid in entity_ids):
                    reasons['role'] = 'Sensor entity did not match any role_inference_rules.'
                elif any(eid.startswith('media_player.') for eid in entity_ids):
                    reasons['role'] = 'Media player entity not covered by role_inference_rules.'
                elif any(eid.startswith('binary_sensor.') for eid in entity_ids):
                    reasons['role'] = 'Binary sensor entity did not match any role_inference_rules.'
                else:
                    reasons['role'] = 'No matching rule or mapping for entity domain.'
        if failed_steps:
            diagnostics.append({
                'cluster_id': cluster.get('cluster_id'),
                'entity_ids': cluster.get('entity_ids', []),
                'failed_steps': failed_steps,
                'reasons': reasons
            })
    # Determine output path in data/ with timestamp
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    base_output = os.path.basename(output_path)
    output_dir = os.path.join(os.path.dirname(__file__), '../data')
    os.makedirs(output_dir, exist_ok=True)
    output_path_with_timestamp = os.path.join(output_dir, f"advanced_unresolved_cluster_diagnostics_{timestamp}.json")
    with open(output_path_with_timestamp, 'w') as f:
        json.dump(diagnostics, f, indent=2)
    print(f"Diagnostics written to {output_path_with_timestamp}")

if __name__ == "__main__":
    main()
