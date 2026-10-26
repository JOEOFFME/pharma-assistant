"""Draft import preserves evidence and never changes or verifies human gold."""

import copy
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from pharma_assistant.data_tools.fetch_pharmacies import load_config
from pharma_assistant.data_tools.nlu_dataset import read_jsonl, validate_rows

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "import_gold_draft", ROOT / "scripts/import_gold_draft.py"
)
IMPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IMPORTER)
CONFIG = load_config(ROOT / "configs/gold_draft.yaml")
DRAFT = ROOT / CONFIG["input_path"]
REVIEW = ROOT / CONFIG["output_path"]
PROPOSALS = read_jsonl(REVIEW)


@pytest.mark.parametrize("row", PROPOSALS, ids=lambda r: r["id"])
def test_each_output_row_spans_and_relations(row: dict) -> None:
    """Raw Unicode spans, non-overlap and all schema/link invariants hold per row."""
    validate_rows([row])
    assert row["verified"] is False
    assert row["source"] == "assistant_seed"
    assert row["split"] == "review_only"
    for entity in row["entities"]:
        assert row["text"][entity["start"] : entity["end"]] == entity["text"]
        assert not entity.get("matched_id") and not entity.get("dci")
    ordered = sorted(row["entities"], key=lambda e: e["start"])
    assert all(
        a["end"] <= b["start"] for a, b in zip(ordered, ordered[1:], strict=False)
    )


def test_every_original_text_and_label_preserved_in_provenance() -> None:
    """There is one proposal per source line, including spelling and label errors."""
    original = IMPORTER.parse_draft(DRAFT)
    assert len(PROPOSALS) == len(original) == 84
    for source, row in zip(original, PROPOSALS, strict=True):
        assert row["text"] == source["text"]
        assert row["language"] == source["language"]
        assert row["draft"]["line_number"] == source["line_number"]
        assert row["draft"]["proposed_intent"] == source["proposed_intent"]
        assert row["draft"]["notes"] == source["notes"]
    assert PROPOSALS[12]["draft"]["proposed_intent"] == "price_inquiry"
    assert PROPOSALS[12]["intent"] == "price_inquiry"
    assert PROPOSALS[62]["draft"]["proposed_intent"] == "check_availability"
    assert PROPOSALS[62]["intent"] == "check_availability"
    assert {e["type"] for r in PROPOSALS for e in r["entities"]} == {
        "MEDICATION",
        "DOSAGE",
        "FORM",
        "QUANTITY",
        "PHARMACY_NAME",
        "LOCATION",
        "TIME_REF",
        "URGENCY",
    }


def test_notes_missing_units_and_mixed_routing() -> None:
    """Missing units are never guessed, and medical-advice clauses stay separate."""
    for row in PROPOSALS:
        notes = row["draft"]["notes"]
        if "needs_clarification" in notes:
            assert row["needs_clarification"] is True
        if "mixed_oos" in notes:
            assert row["contains_out_of_scope_request"] is True
            assert row["intent"] == "check_availability"
        for entity in row["entities"]:
            if entity["type"] == "DOSAGE" and entity["text"].isdigit():
                assert entity.get("value") is None and entity.get("unit") is None
                if row["intent"] != "out_of_scope":
                    assert row["needs_clarification"] is True
    bare_counts = [
        e
        for r in PROPOSALS
        for e in r["entities"]
        if e["type"] == "QUANTITY" and e["text"].isdigit()
    ]
    assert bare_counts and all(e["unit"] == "unit" for e in bare_counts)
    assert PROPOSALS[75]["draft"]["review_notes"]  # Packaging is not a FORM.


def test_clitic_and_time_boundaries() -> None:
    """Exclude generic pharmacy prefixes, f-/l'/d' and retain whole time phrases."""

    def span(index: int, kind: str) -> list[str]:
        return [
            e["text"] for e in PROPOSALS[index - 1]["entities"] if e["type"] == kind
        ]

    assert span(15, "PHARMACY_NAME") == ["Ibn Sina"]
    assert span(38, "LOCATION") == ["كازا"]
    assert span(41, "LOCATION") == ["طنجة"]
    assert span(48, "MEDICATION") == ["amoxicilline"]
    assert span(50, "MEDICATION") == ["Efferalgan"]
    assert span(56, "TIME_REF") == ["ce soir"]
    assert span(81, "TIME_REF") == ["had lila"]


def isolated_config(tmp_path: Path) -> dict:
    """Configure all writes under a temporary directory, with protected sentinel."""
    config = copy.deepcopy(CONFIG)
    gold = tmp_path / "gold_human.jsonl"
    gold.write_bytes(b"human gold sentinel: never overwrite\n")
    config.update(
        input_path=str(DRAFT),
        output_path=str(tmp_path / "gold_review.jsonl"),
        report_path=str(tmp_path / "review.md"),
        protected_gold_path=str(gold),
        dataset_dir=str(tmp_path / "absent"),
    )
    return config


def test_reproducible_import_full_table_and_gold_unchanged(tmp_path: Path) -> None:
    """Regeneration is deterministic and protected gold remains byte-identical."""
    config = isolated_config(tmp_path)
    source_before = DRAFT.read_bytes()
    gold_before = Path(config["protected_gold_path"]).read_bytes()
    rows = IMPORTER.import_draft(config)
    before = Path(config["output_path"]).read_bytes()
    table = Path(config["report_path"]).read_text()
    assert (
        len([line for line in table.splitlines() if line.startswith("| draft_review_")])
        == 84
    )
    assert table == IMPORTER.review_table(rows)
    with pytest.raises(ValueError, match="exists"):
        IMPORTER.import_draft(config)
    assert IMPORTER.import_draft(config, overwrite=True) == rows
    assert Path(config["output_path"]).read_bytes() == before
    assert Path(config["protected_gold_path"]).read_bytes() == gold_before
    assert DRAFT.read_bytes() == source_before


@pytest.mark.parametrize("destination", ["output_path", "report_path"])
def test_gold_write_and_symlink_paths_refused(tmp_path: Path, destination: str) -> None:
    """Even --overwrite cannot aim a proposal or report at protected human gold."""
    config = isolated_config(tmp_path)
    gold = Path(config["protected_gold_path"])
    original = gold.read_bytes()
    config[destination] = str(gold)
    with pytest.raises(ValueError, match="Refusing"):
        IMPORTER.import_draft(config, overwrite=True)
    alias = tmp_path / "alias.jsonl"
    alias.symlink_to(gold)
    config[destination] = str(alias)
    with pytest.raises(ValueError, match="Refusing"):
        IMPORTER.import_draft(config, overwrite=True)
    hardlink = tmp_path / "hardlink.jsonl"
    hardlink.hardlink_to(gold)
    config[destination] = str(hardlink)
    with pytest.raises(ValueError, match="Refusing"):
        IMPORTER.import_draft(config, overwrite=True)
    assert gold.read_bytes() == original


def test_parser_preserves_whitespace_pipes_unicode_and_repeated_mentions(
    tmp_path: Path,
) -> None:
    """Only one format padding space is consumed; source characters stay untouched."""
    source = tmp_path / "draft.txt"
    text = " 🙂 é l'amoxicilline 500 mg | Doliprane puis Doliprane  "
    source.write_bytes(
        (
            "# comment\r\nfr | request_medication | multi_med,dosage | " + text + "\r\n"
        ).encode()
    )
    parsed = IMPORTER.parse_draft(source)
    assert parsed[0]["text"] == text
    row = IMPORTER.propose(parsed[0], CONFIG, 1)
    validate_rows([row])
    assert [e["text"] for e in row["entities"] if e["type"] == "MEDICATION"] == [
        "amoxicilline",
        "Doliprane",
        "Doliprane",
    ]
    for e in row["entities"]:
        assert text[e["start"] : e["end"]] == e["text"]


def test_malformed_draft_does_not_write_partial_output(tmp_path: Path) -> None:
    """Invalid rows abort before any output file or human gold is modified."""
    config = isolated_config(tmp_path)
    source = tmp_path / "bad.txt"
    source.write_text(
        "fr | check_availability | | Doliprane ?\nthis line is malformed\n"
    )
    config["input_path"] = str(source)
    with pytest.raises(ValueError, match="Line 2"):
        IMPORTER.import_draft(config)
    assert not Path(config["output_path"]).exists()
    assert not Path(config["report_path"]).exists()


def test_cli_prints_every_row(tmp_path: Path) -> None:
    """Actual CLI produces the full table, not just a count or a sample."""
    import yaml

    config = isolated_config(tmp_path)
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config, allow_unicode=True))
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/import_gold_draft.py"),
            "--config",
            str(path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.count("| draft_review_") == 84
    assert "all verified=false" in result.stdout
    assert "gold_human.jsonl untouched" in result.stdout


def test_print_existing_preserves_corrected_rows_and_refuses_text_edits(
    tmp_path: Path,
) -> None:
    """A correction can be inspected without regeneration; text changes are rejected."""
    import yaml

    config = isolated_config(tmp_path)
    IMPORTER.import_draft(config)
    output = Path(config["output_path"])
    rows = read_jsonl(output)
    rows[12]["needs_clarification"] = True  # Human can correct a proposed annotation.
    from pharma_assistant.data_tools.nlu_dataset import write_jsonl

    write_jsonl(output, rows)
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config, allow_unicode=True))
    before = output.read_bytes()
    report_before = Path(config["report_path"]).read_bytes()
    command = [
        sys.executable,
        str(ROOT / "scripts/import_gold_draft.py"),
        "--config",
        str(path),
        "--print-existing",
    ]
    result = subprocess.run(
        command, cwd=ROOT, capture_output=True, text=True, check=True
    )
    assert result.stdout.count("| draft_review_") == 84
    assert output.read_bytes() == before
    assert Path(config["report_path"]).read_bytes() == report_before
    rows[12]["text"] += " "
    write_jsonl(output, rows)
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    assert result.returncode != 0 and "preserve all source texts" in result.stderr
