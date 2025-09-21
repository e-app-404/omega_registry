from datetime import datetime

def estimate_duration_from_log(log_path, phase_desc):
    """
    Simple estimation: find first and last timestamp for phase in log.
    """
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

def aggregate_metric(snapshot, keys, mode='max'):
    result = 0 if mode == 'max' else 0
    for phase in snapshot.get('phases', {}).values():
        m = phase.get('metrics', {})
        for k in keys:
            v = m.get(k)
            if v and isinstance(v, int):
                if mode == 'max':
                    result = max(result, v)
                elif mode == 'sum':
                    result += v
    return result

def compute_summary(snapshot):
    total_entities = aggregate_metric(snapshot, ['pre_reboot_entities', 'input_entities', 'output_entities', 'total_entities_fingerprinted'], mode='max')
    final_entities_included = aggregate_metric(snapshot, ['entities_included', 'output_entities', 'post_reboot_entities'], mode='max')
    final_clusters = aggregate_metric(snapshot, ['clusters_generated', 'unique_clusters'], mode='max')
    area_success = aggregate_metric(snapshot, ['area_inferred_entities'], mode='sum')
    area_total = aggregate_metric(snapshot, ['input_entities'], mode='sum')
    role_success = aggregate_metric(snapshot, ['roles_inferred'], mode='sum')
    role_total = aggregate_metric(snapshot, ['input_entities'], mode='sum')
    overall_duration = 0
    for phase in snapshot.get('phases', {}).values():
        m = phase.get('metrics', {})
        try:
            d = m.get('duration_seconds')
            if isinstance(d, (int, float)):
                overall_duration += d
            elif isinstance(d, str) and d.replace('.', '', 1).isdigit():
                overall_duration += float(d)
        except Exception:
            pass
    area_rate = round(area_success / area_total, 4) if area_total else ''
    role_rate = round(role_success / role_total, 4) if role_total else ''
    avg_per_cluster = round(final_entities_included / final_clusters, 2) if final_clusters else ''
    return {
        'total_entities_processed': total_entities,
        'final_entities_included': final_entities_included,
        'final_clusters': final_clusters,
        'area_inference_success_rate': area_rate,
        'role_inference_success_rate': role_rate,
        'avg_entities_per_cluster': avg_per_cluster,
        'overall_duration_seconds': round(overall_duration, 2)
    }

def normalize_phase_metrics(phase, log_path=None):
    """
    Normalize and fill missing or blank metrics fields for a phase dict.
    Optionally estimate duration from log if not present.
    """
    m = phase.setdefault('metrics', {})
    # Normalize duration_seconds
    if 'duration_seconds' not in m or not m['duration_seconds']:
        if log_path and 'description' in phase:
            est = estimate_duration_from_log(log_path, phase.get('description', ''))
            if est:
                m['duration_seconds'] = round(est, 2)
            else:
                m['duration_seconds'] = ''
        else:
            m['duration_seconds'] = ''
    # Normalize status
    if 'status' not in phase or not phase['status']:
        phase['status'] = m.get('status', '')
    # Normalize validation_status
    if 'validation_status' not in m:
        m['validation_status'] = phase.get('validation', {}).get('status', '')
    # Normalize terminal
    if 'terminal' not in phase or not phase['terminal']:
        phase['terminal'] = ''
    return phase

# --- Entity Breakdown Utilities ---
# def breakdown_by_field(entities, field):
#     """
#     Returns a dict with counts of entities by the specified field (e.g., 'role', 'semantic_role', 'type').
#     """
#     from collections import Counter
#     values = [e.get(field, 'unknown') for e in entities]
#     return dict(Counter(values))
