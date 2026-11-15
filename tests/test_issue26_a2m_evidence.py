from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "data" / "pharmacology_evidence_audit.csv"
DOC = ROOT / "docs" / "A2M_EVIDENCE_AUDIT.md"


def test_a2m_primary_prognostic_record_is_pinned():
    rows = list(csv.DictReader(AUDIT.open(newline="", encoding="utf-8")))
    row = next(r for r in rows if r["candidate"] == "A2M" and r["pmid"] == "39005669")
    assert row["doi"] == "10.62347/VUJV9180"
    assert row["manuscript_status"] == "Contextual / exploratory"
    assert "expression and survival" in row["supported_claim"]


def test_a2m_subtype_proteomics_record_is_pinned():
    rows = list(csv.DictReader(AUDIT.open(newline="", encoding="utf-8")))
    row = next(r for r in rows if r["pmid"] == "27498393")
    assert row["doi"] == "10.1016/j.jprot.2016.07.033"
    assert "triple-negative" in row["supported_claim"]


def test_a2m_audit_forbids_therapeutic_upgrade():
    text = DOC.read_text(encoding="utf-8")
    assert "retains A2M as **Contextual / exploratory**" in text
    assert "Not supported by the cited evidence" in text
    assert "A2M is an approved or established breast-cancer drug target" in text
