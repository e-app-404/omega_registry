import json
import yaml
import os
from datetime import datetime
from registry.utils.metrics import aggregate_metric, compute_summary

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def save_json(obj, path):
    with open(path, 'w') as f:
        json.dump(obj, f, indent=2)

def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def save_yaml(obj, path):
    with open(path, 'w') as f:
        yaml.dump(obj, f, sort_keys=False)

def estimate_duration_from_log(log_path, phase_desc):
    # Simple estimation: find first and last timestamp for phase in log
    try:
        with open(log_path) as f:
            lines = f.readlines()
        times = []
        for line in lines:
            if phase_desc in line:
                # Expect format: [YYYY-MM-DD HH:MM:SS] ...
                if line.startswith('['):
                    ts = line[1:20]
                    try:
                        dt = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
                        times.append(dt)
                    except Exception:
                        continue
        if times:
            return (max(times) - min(times)).total_seconds()
    except Exception:
        pass
    return None

def main():
    metrics_path = 'data/pipeline_metrics.latest.json'
    snapshot_path = 'data/pipeline_run_snapshot.20250719T020000.yaml'
    log_path = 'copilot_patchlog_overview.log'
    out_dir = 'output/pipeline_metrics'
    os.makedirs(out_dir, exist_ok=True)
    # Load data
    metrics = load_json(metrics_path)
    snapshot = load_yaml(snapshot_path)
    # Normalize and update per-phase stats
    for phase_num, phase in snapshot.get('phases', {}).items():
        # Normalize duration
        if 'duration_seconds' not in phase['metrics'] or not phase['metrics']['duration_seconds']:
            est = estimate_duration_from_log(log_path, phase.get('description', ''))
            if est:
                phase['metrics']['duration_seconds'] = round(est, 2)
            else:
                phase['metrics']['duration_seconds'] = ''
        # Normalize status
        if 'status' not in phase or not phase['status']:
            phase['status'] = phase['metrics'].get('status', '')
        # Normalize validation_status
        if 'validation_status' not in phase['metrics']:
            phase['metrics']['validation_status'] = phase.get('validation', {}).get('status', '')
        # Normalize terminal
        if 'terminal' not in phase or not phase['terminal']:
            phase['terminal'] = ''
    # Compute and update summary
    summary = compute_summary(snapshot)
    metrics['summary'] = summary
    # Save updated files
    save_yaml(snapshot, snapshot_path)
    save_json(metrics, metrics_path)
    # Emit phase duration report
    phase_report = {}
    for phase_num, phase in snapshot.get('phases', {}).items():
        phase_report[phase_num] = {
            'description': phase.get('description', ''),
            'duration_seconds': phase['metrics'].get('duration_seconds', ''),
            'status': phase.get('status', ''),
        }
    save_json(phase_report, os.path.join(out_dir, 'phase_duration_report.log'))
    # Emit execution summary snapshot
    save_json(summary, os.path.join(out_dir, 'execution_summary_snapshot.json'))
    print('Phase 10 metrics audit complete. All outputs updated.')

if __name__ == '__main__':
    main()
