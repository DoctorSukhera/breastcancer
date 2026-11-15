from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "reference_corrections.csv"


def test_liu_alkbh5_foxo1_canonical_record():
    rows = list(csv.DictReader(REGISTRY.open(newline="", encoding="utf-8")))
    row = next(r for r in rows if r["citation_key"] == "Liu2024_ALKBH5_FOXO1")
    assert row["pmid"] == "38104484"
    assert row["journal"] == "Redox Biology"
    assert row["volume"] == "69"
    assert row["year"] == "2024"
    assert row["correct_article_number"] == "102993"
    assert row["correct_doi"] == "10.1016/j.redox.2023.102993"
    assert row["known_incorrect_article_number"] == "102999"
    assert row["verification_status"] == "verified_against_pubmed_and_elsevier"


def test_wrong_foxxo1_doi_not_used_as_canonical():
    rows = list(csv.DictReader(REGISTRY.open(newline="", encoding="utf-8")))
    row = next(r for r in rows if r["citation_key"] == "Liu2024_ALKBH5_FOXO1")
    assert row["correct_doi"] != "10.1016/j.redox.2023.102999"
