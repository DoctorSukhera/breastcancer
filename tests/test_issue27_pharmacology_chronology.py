from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]


def test_chronology_audit_marks_layer_revision_added():
    p = ROOT / 'data' / 'pharmacology_chronology_audit.csv'
    rows = list(csv.DictReader(p.open(encoding='utf-8')))
    assert len(rows) >= 3
    assert {r['chronology_status'] for r in rows} == {'revision_added'}
    assert all('prespecified' not in r['corrected_wording'].lower() or 'rather than as a prespecified validation endpoint' in r['corrected_wording'].lower() for r in rows)


def test_change_log_forbids_prespecified_pharmacology_claim():
    text = (ROOT / 'ISSUE27_MANUSCRIPT_CHANGES.txt').read_text(encoding='utf-8')
    assert 'subjected during peer-review revision to a structured pharmacological contextualization step' in text
    assert 'Applying this revision-added follow-up interpretation' in text
    # Old wording is retained only inside the explicitly labelled OLD audit blocks.
    assert text.count('prespecified pharmacological contextualization step') == 1
    assert text.count('Applying the prespecified follow-up interpretation') == 1


def test_audit_states_no_scientific_result_change():
    text = (ROOT / 'docs' / 'PHARMACOLOGY_CHRONOLOGY_AUDIT.md').read_text(encoding='utf-8')
    for required in [
        'TCGA-BRCA age-association results',
        'GSE42568 replication results',
        'Class A–D assignments',
        'follow-up routes',
        'does not modify any quantitative output',
    ]:
        assert required in text
