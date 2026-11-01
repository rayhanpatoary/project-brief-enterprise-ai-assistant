import json

from scripts.evaluate import main


def test_repeatable_evaluation_reports_measured_hits(populated, monkeypatch, capsys, tmp_path):
    dataset = tmp_path / 'cases.json'
    dataset.write_text(json.dumps([
        {'question': 'remote days?', 'expected_sources': ['policy.md'], 'insufficient': False},
        {'question': 'profit?', 'expected_sources': [], 'insufficient': True},
    ]), encoding='utf-8')
    monkeypatch.setattr('sys.argv', ['evaluate', '--dataset', str(dataset)])
    monkeypatch.setattr('scripts.evaluate.KnowledgeStore', lambda _: populated)
    main()
    result = json.loads(capsys.readouterr().out)
    assert result['positive_cases'] == 1 and result['retrieval_hit_rate'] == 1
    assert result['abstention_rate'] is None
    assert len(result['cases']) == 2
