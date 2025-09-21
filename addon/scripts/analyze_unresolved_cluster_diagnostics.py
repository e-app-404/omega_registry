import json
from collections import Counter, defaultdict
import sys

# Usage: python scripts/analyze_unresolved_cluster_diagnostics.py <unresolved_cluster_diagnostics.json>
def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/analyze_unresolved_cluster_diagnostics.py <unresolved_cluster_diagnostics.json>")
        sys.exit(1)
    input_path = sys.argv[1]
    with open(input_path, 'r') as f:
        diagnostics = json.load(f)
    area_only = 0
    role_only = 0
    both = 0
    total = len(diagnostics)
    failed_step_combos = Counter()
    reason_counter = defaultdict(Counter)
    domain_counter = Counter()
    for d in diagnostics:
        steps = tuple(sorted(d['failed_steps']))
        failed_step_combos[steps] += 1
        for step in d['failed_steps']:
            reason = d['reasons'].get(step, 'unknown')
            reason_counter[step][reason] += 1
        # Domain analysis
        for eid in d['entity_ids']:
            domain = eid.split('.', 1)[0] if '.' in eid else 'unknown'
            domain_counter[domain] += 1
    print(f"Total unresolved clusters: {total}")
    print("\nBreakdown by failed step(s):")
    for steps, count in failed_step_combos.items():
        print(f"  {steps}: {count}")
    print("\nMost common reasons for area failure:")
    for reason, count in reason_counter['area'].most_common():
        print(f"  {reason}: {count}")
    print("\nMost common reasons for role failure:")
    for reason, count in reason_counter['role'].most_common():
        print(f"  {reason}: {count}")
    print("\nEntity domain breakdown:")
    for domain, count in domain_counter.most_common():
        print(f"  {domain}: {count}")

if __name__ == "__main__":
    main()
