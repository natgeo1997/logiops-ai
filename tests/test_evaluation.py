from pathlib import Path
import pytest
from evaluation.run import baseline, load_cases, score

CASES = load_cases(Path(__file__).resolve().parents[1] / 'evaluation/cases.json')


def test_constant_baseline_scores_25_percent_on_balanced_cases():
    result = score(CASES, baseline(CASES))
    assert result['case_count'] == 12
    assert result['priority_accuracy'] == 0.25
    assert result['valid_response_rate'] == 1
    assert result['reference_priority_counts'] == {'Critical': 3, 'High': 3, 'Medium': 3, 'Low': 3}


def test_missing_and_failed_responses_remain_in_denominator():
    rows = baseline(CASES)
    for row, case in zip(rows, CASES):
        row['assessment']['priority'] = case['expected_priority']
    rows.pop()
    rows[0] = {'id': CASES[0]['id'], 'error': 'provider_or_validation_failure'}
    result = score(CASES, rows)
    assert result['case_count'] == 12
    assert result['valid_response_rate'] == 10 / 12
    assert result['priority_accuracy'] == 10 / 12


@pytest.mark.parametrize('rows', [[{'id': 'unknown'}], [{'id': 'critical-01'}, {'id': 'critical-01'}]])
def test_duplicate_or_unknown_response_ids_rejected(rows):
    with pytest.raises(ValueError):
        score(CASES, rows)


def test_action_count_and_schema_are_distinct_checks():
    rows = baseline(CASES)
    rows[0]['assessment']['recommended_actions'] = ['Only one']
    result = score(CASES, rows)
    assert result['valid_response_rate'] == 1
    assert result['action_count_compliance_rate'] == 11 / 12
