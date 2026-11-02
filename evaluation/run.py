"""Small, synthetic priority benchmark. No API call unless --live is selected."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import Avaliacao, analisar


def load_cases(path):
    cases = json.loads(Path(path).read_text())
    ids = [case['id'] for case in cases]
    if not cases or len(set(ids)) != len(ids):
        raise ValueError('Cases must have unique IDs and cannot be empty')
    for case in cases:
        if case['expected_priority'] not in ('Critical', 'High', 'Medium', 'Low'):
            raise ValueError('Unsupported reference priority')
    return cases


def score(cases, responses):
    known = {case['id'] for case in cases}
    by_id = {}
    for response in responses:
        identifier = response['id']
        if identifier not in known or identifier in by_id:
            raise ValueError('Unknown or duplicate response ID')
        by_id[identifier] = response
    rows = []
    for case in cases:
        response = by_id.get(case['id'], {})
        try:
            assessment = Avaliacao.model_validate(response.get('assessment'))
            valid = True
        except (ValueError, TypeError):
            assessment, valid = None, False
        priority = assessment.priority if valid else None
        rows.append({'id': case['id'], 'expected_priority': case['expected_priority'],
                     'predicted_priority': priority, 'schema_valid': valid,
                     'priority_correct': valid and priority == case['expected_priority'],
                     'action_count_in_prompt_range': bool(valid and 3 <= len(assessment.recommended_actions) <= 6 and 2 <= len(assessment.preventive_actions) <= 4),
                     'latency_seconds': response.get('latency_seconds'),
                     'review_focus': case['review_focus']})
    total = len(rows)
    latency = [row['latency_seconds'] for row in rows if isinstance(row['latency_seconds'], (int, float)) and row['latency_seconds'] >= 0]
    return {'case_count': total,
            'reference_priority_counts': dict(Counter(case['expected_priority'] for case in cases)),
            'valid_response_rate': sum(row['schema_valid'] for row in rows) / total,
            'priority_accuracy': sum(row['priority_correct'] for row in rows) / total,
            'action_count_compliance_rate': sum(row['action_count_in_prompt_range'] for row in rows) / total,
            'median_latency_seconds': statistics.median(latency) if latency else None,
            'cases': rows}


def baseline(cases):
    # An intentionally simple comparator, not an AI model.
    return [{'id': case['id'], 'assessment': {
        'priority': 'Medium', 'operational_impact': 'Baseline placeholder.',
        'root_cause': 'Baseline placeholder.', 'recommended_actions': ['Review the report.'] * 3,
        'preventive_actions': ['Review the process.'] * 2,
        'suggested_communication': 'Baseline placeholder.'}} for case in cases]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--baseline', action='store_true')
    mode.add_argument('--responses', type=Path, help='Score a captured response JSON array')
    mode.add_argument('--live', action='store_true', help='Call Gemini once per case; may incur provider charges')
    parser.add_argument('--cases', type=Path, default=ROOT / 'evaluation/cases.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--model', default=os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash'))
    args = parser.parse_args()
    cases = load_cases(args.cases)
    captured = []
    if args.live:
        key = os.environ.get('GEMINI_API_KEY', '').strip()
        if not key:
            parser.error('Set GEMINI_API_KEY before running --live. No calls were made.')
        for case in cases:
            start = time.monotonic()
            try:
                result = analisar(case['report'], key, args.model)
                captured.append({'id': case['id'], 'assessment': result.model_dump(), 'latency_seconds': round(time.monotonic()-start, 3)})
            except Exception:
                # Failed calls remain in the denominator. Do not persist raw errors or secrets.
                captured.append({'id': case['id'], 'error': 'provider_or_validation_failure', 'latency_seconds': round(time.monotonic()-start, 3)})
    elif args.baseline:
        captured = baseline(cases)
    else:
        captured = json.loads(args.responses.read_text())
    result = score(cases, captured)
    result['run'] = {'mode': 'gemini-live' if args.live else 'constant-Medium-baseline' if args.baseline else 'captured-responses',
                     'model': args.model if args.live else None,
                     'created_at': datetime.now(timezone.utc).isoformat(),
                     'scope': 'Synthetic hand-labelled fixture; no claim of production performance or semantic correctness.'}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'metrics.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    (args.output / 'responses.json').write_text(json.dumps(captured, ensure_ascii=False, indent=2)+'\n')
    review = [{'id': case['id'], 'review_focus': case['review_focus'],
               'factual_grounding_0_to_2': None, 'uncertainty_0_to_2': None,
               'actionability_0_to_2': None, 'human_control_0_to_2': None, 'reviewer_notes': ''} for case in cases]
    (args.output / 'human-review.json').write_text(json.dumps(review, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'cases'}, indent=2))


if __name__ == '__main__':
    main()
