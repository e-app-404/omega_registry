import json
import sys

# Usage: python scripts/emit_unresolved_cluster_diagnostics.py <input_alpha_sensor_registry.json> <output_diagnostics.json>
def main():
    if len(sys.argv) != 3:
        print("Usage: python scripts/emit_unresolved_cluster_diagnostics.py <input_alpha_sensor_registry.json> <output_diagnostics.json>")
        sys.exit(1)
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    with open(input_path, 'r') as f:
        clusters = json.load(f)
    diagnostics = []
    for cluster in clusters:
        failed_steps = []
        if cluster.get('final_area', None) == 'unknown_area':
            failed_steps.append('area')
        if cluster.get('role', None) in ('unclassified', 'diagnostic', None, ''):
            failed_steps.append('role')
        if failed_steps:
            diagnostics.append({
                'cluster_id': cluster.get('cluster_id'),
                'entity_ids': cluster.get('entity_ids', []),
                'failed_steps': failed_steps
            })
    with open(output_path, 'w') as f:
        json.dump(diagnostics, f, indent=2)

if __name__ == "__main__":
    main()
