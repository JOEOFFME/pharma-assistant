"""Reference-data integrity and name-retrieval tests; no clinical advice is tested."""

import copy
import gzip
import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from pharma_assistant.data.medications import MedicationRepository
from pharma_assistant.data_tools.fetch_pharmacies import load_config
from pharma_assistant.data_tools.ingest_medications import (
    build_medications,
    parse_rows,
    published_dates,
    read_snapshot,
)
from pharma_assistant.data_tools.medication_names import (
    generate_aliases,
    latin_to_arabic,
    phonetic_key,
)
from pharma_assistant.eval.medication_resolution import evaluate
from pharma_assistant.matching.medications import MedicationIndex, strength_tokens

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def built(tmp_path_factory: pytest.TempPathFactory) -> tuple:
    """Rebuild real data in isolation without a request to the upstream server."""
    config = load_config(ROOT / "configs/medications.yaml")
    directory = tmp_path_factory.mktemp("medications")
    config.update(
        snapshot_dir=str(ROOT / config["snapshot_dir"]),
        database_path=str(directory / "medications.sqlite3"),
        metrics_path=str(directory / "metrics.json"),
        results_path=str(directory / "results.json"),
        report_path=str(directory / "report.md"),
        queries_path=str(ROOT / config["queries_path"]),
    )
    metrics = build_medications(config)
    rows = MedicationRepository(Path(config["database_path"])).all()
    return config, metrics, MedicationIndex(rows, config["matching"]), directory


@pytest.mark.parametrize(
    "query", ["Doliprane", "dolipran", "دوليبران", "doliprane 1000"]
)
def test_requested_name_variants(built: tuple, query: str) -> None:
    """Required spelling/script queries find source-backed candidate names."""
    hits = built[2].search(query, k=3)
    assert hits and hits[0].medication.brand_name == "DOLIPRANE"
    assert hits[0].medication.source.country == "FR"
    assert all(hit.needs_clarification for hit in hits)
    if "1000" in query:
        assert all("1000" in hit.medication.full_name for hit in hits)


@pytest.mark.parametrize(
    "query,amount",
    [
        ("Doliprane 500 mg comprimé", 500),
        ("Doliprane 1000 mg comprimé", 1000),
        ("Doliprane 1 g comprimé", 1000),
        ("دوليبران ٥٠٠ mg", 500),
    ],
)
def test_strength_disambiguation(built: tuple, query: str, amount: int) -> None:
    """Explicit strength must not resolve to a conflicting product strength."""
    hits = built[2].search(query)
    assert hits and hits[0].medication.brand_name == "DOLIPRANE"
    for hit in hits:
        assert (amount, "mg", "") in strength_tokens(hit.medication.full_name)
        assert hit.strength_match is True


def test_missing_strength_is_not_inferred(built: tuple) -> None:
    """Bare brands remain ambiguous; impossible strengths return no hit."""
    assert built[2].search("Doliprane")[0].needs_clarification
    assert built[2].search("Doliprane 999999 mg") == []
    assert built[2].search("zzqxvbnm") == []
    assert built[2].search("   ") == []
    assert built[2].search("500") == []


@pytest.mark.parametrize("query", [None, 42, "x" * 501])
def test_invalid_queries(built: tuple, query: object) -> None:
    """Reject invalid/oversized input rather than silently stringifying it."""
    with pytest.raises(ValueError):
        built[2].search(query)


@pytest.mark.parametrize("k", [0, -1, 101, True, 2.5])
def test_invalid_k(built: tuple, k: object) -> None:
    """Keep candidate counts bounded and integral."""
    with pytest.raises(ValueError):
        built[2].search("Doliprane", k=k)


def test_strength_units_concentrations_and_combinations() -> None:
    """Concentrations cannot collapse to plain mass; combinations retain both values."""
    assert strength_tokens("1 g") == strength_tokens("1000 mg")
    assert strength_tokens("500 microgrammes") == {(0.5, "mg", "")}
    assert strength_tokens("1 mg/ml") != {(1.0, "mg", "")}
    assert strength_tokens("1 g/125 mg") == {(1000.0, "mg", ""), (125.0, "mg", "")}
    assert strength_tokens("2,4 POUR CENT") == {(2.4, "%", "")}


def test_synthetic_alias_provenance() -> None:
    """Source spellings and generated Arabic/typo spellings cannot be conflated."""
    aliases = generate_aliases("DOLIPRANE", "DOLIPRANE 500 mg, comprimé", "500 mg")
    assert latin_to_arabic("DOLIPRANE") == "دوليبران"
    assert phonetic_key("دوليبران") == phonetic_key("doliprane")
    assert phonetic_key("3afak 500 mg").endswith("500 mg")
    assert any(
        a["kind"] == "arabic_transliteration" and a["synthetic"] for a in aliases
    )
    assert all(a["synthetic"] for a in aliases if a["kind"] != "source")
    assert len({a["text"] for a in aliases}) == len(aliases)


def test_ingestion_is_fact_based_and_country_explicit(built: tuple) -> None:
    """Imported counts/provenance are reproducible; absent Moroccan facts stay null."""
    config, metrics, index, _ = built
    saved = json.loads((ROOT / "docs/medication_metrics.json").read_text())
    assert metrics == saved
    assert len(index.records) == metrics["records"] == 15883
    assert all(
        row.price_ppv is None and row.brand_name_ar is None
        for row in index.records.values()
    )
    row = index.records["bdpm_fr_60234100"]
    assert row.dci and row.dci in {
        part["substance"] for part in row.composition if part["nature"] == "SA"
    }
    assert row.source.country == "FR" and row.source.source_updated == "2026-09-29"
    assert all(
        row.source.raw_sha256 == saved["source"]["files"]["CIS_bdpm.txt"]["sha256"]
        for row in index.records.values()
    )
    assert all(0 <= hit.score <= 1 for hit in index.search("Doliprane"))
    compound = next(
        row
        for row in index.records.values()
        if row.full_name.startswith("AUGMENTIN 1 g/125 mg,")
    )
    assert compound.dosage == "1 g/125 mg"
    with sqlite3.connect(config["database_path"]) as connection:
        assert (
            connection.execute("SELECT COUNT(*) FROM medication_aliases").fetchone()[0]
            == metrics["aliases"]
        )


def test_reference_file_shape_and_encodings() -> None:
    """Tab count and CIS identity drift must fail loudly; encodings remain explicit."""
    raw = "12345678\tcomprimé\r\n".encode("cp1252")
    assert parse_rows(raw, "cp1252", 2)[0][1] == "comprimé"
    with pytest.raises(ValueError):
        parse_rows(raw, "cp1252", 3)
    with pytest.raises(UnicodeDecodeError):
        parse_rows(raw, "utf-8", 2)
    with pytest.raises(ValueError):
        parse_rows(b"bad\trow\n", "utf-8", 2)


def test_source_page_dates_and_tamper_detection(tmp_path: Path) -> None:
    """Hashes protect original bytes; missing upstream dates do not become guesses."""
    source = ROOT / "data/raw/bdpm_snapshot"
    manifest, contents = read_snapshot(source)
    page = (source / "download_page.html").read_text()
    dates = published_dates(page, manifest["files"])
    assert dates["CIS_CIP_bdpm.txt"] == "2026-10-26"
    with pytest.raises(ValueError):
        published_dates("<html></html>", manifest["files"])
    local = tmp_path / "snapshot"
    local.mkdir()
    (local / "download_page.html").write_text(page)
    bad = copy.deepcopy(manifest)
    key = "CIS_bdpm.txt"
    bad["files"] = {key: bad["files"][key]}
    (local / "manifest.json").write_text(json.dumps(bad))
    archive = gzip.compress(contents[key] + b"tamper", mtime=0)
    (local / bad["files"][key]["archive"]).write_bytes(archive)
    with pytest.raises(ValueError, match="Archive hash"):
        read_snapshot(local)
    bad["files"][key]["archive_sha256"] = hashlib.sha256(archive).hexdigest()
    (local / "manifest.json").write_text(json.dumps(bad))
    with pytest.raises(ValueError, match="Source hash"):
        read_snapshot(local)


def test_empty_index_and_config_constraints(built: tuple) -> None:
    """Empty catalogues and invalid configuration cannot manufacture candidates."""
    config = built[0]["matching"]
    assert MedicationIndex([], config).search("Doliprane") == []
    bad = {**config, "fuzzy_weight": -1}
    with pytest.raises(ValueError):
        MedicationIndex([], bad)
    bad = {**config, "retrieval_aliases": 0}
    with pytest.raises(ValueError):
        MedicationIndex([], bad)


def test_repeated_build_is_idempotent_and_missing_db_fails(
    built: tuple, tmp_path: Path
) -> None:
    """Rebuilds avoid duplicates; read typos never create database files."""
    config, metrics, _, _ = built
    assert build_medications(config) == metrics
    missing = tmp_path / "missing.sqlite3"
    with pytest.raises(FileNotFoundError):
        MedicationRepository(missing).all()
    assert not missing.exists()


def test_saved_fifty_query_evaluation_is_traceable(built: tuple) -> None:
    """Recompute metrics from candidate IDs and compare against the saved artifact."""
    config, _, index, directory = built
    result = evaluate(config)
    saved = json.loads((ROOT / "docs/medication_query_results.json").read_text())
    assert result == saved
    queries = json.loads(
        (ROOT / "docs/examples/medication_queries_50.json").read_text()
    )
    assert len(queries) == 50 and all(
        row["review_status"] == "pending_user_review" for row in queries
    )
    assert all(set(row["expected_ids"]).issubset(index.records) for row in queries)
    assert (
        sum(row["top1_correct"] for row in result["predictions"])
        == result["summary"]["top1_correct"]
    )
    assert (
        sum(row["top3_correct"] for row in result["predictions"])
        == result["summary"]["top3_correct"]
    )
    assert (directory / "report.md").read_text() == (
        ROOT / "docs/data_medications.md"
    ).read_text()
