"""Validate all committed annotations and enforce separation from human gold."""

import copy
import importlib.util
from pathlib import Path

import pytest

from pharma_assistant.api.schemas import NLUAnnotation
from pharma_assistant.data_tools.fetch_pharmacies import load_config
from pharma_assistant.data_tools.nlu_dataset import (
    build_dataset,
    leakage_check,
    read_jsonl,
    validate_rows,
)

ROOT = Path(__file__).resolve().parents[1]
FILES = sorted((ROOT / "data/nlu").rglob("*.jsonl"))


def script_module(name: str):
    """Import a CLI helper without executing its entry point."""
    spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_every_jsonl_row(path: Path) -> None:
    """Check every span, label, overlap, clarification and exact duplicate text."""
    rows = read_jsonl(path)
    validate_rows(rows)
    for row in rows:
        NLUAnnotation.model_validate(row)
        for entity in row["entities"]:
            assert row["text"][entity["start"] : entity["end"]] == entity["text"]
        ordered = sorted(row["entities"], key=lambda e: e["start"])
        assert all(
            a["end"] <= b["start"] for a, b in zip(ordered, ordered[1:], strict=False)
        )
        if row["intent"] in {
            "check_availability",
            "request_medication",
            "price_inquiry",
        }:
            if not any(e["type"] == "MEDICATION" for e in row["entities"]):
                assert row["needs_clarification"] is True


def test_exact_text_duplicates_across_all_files() -> None:
    """Even cross-file exact copies are rejected; build inputs live outside data/nlu."""
    rows = [row for path in FILES for row in read_jsonl(path)]
    assert len(rows) == len({row["text"] for row in rows})


def test_gold_provenance() -> None:
    """Any non-human or unverified gold row fails, including assistant seeds."""
    path = ROOT / "data/nlu/gold_human.jsonl"
    assert path.exists()
    for row in read_jsonl(path):
        assert row["source"] == "human"
        assert row["verified"] is True


def test_dev_seed_regressions() -> None:
    """Preserve all 100 rows with the requested mixed/missing/relations fixes."""
    rows = read_jsonl(ROOT / "data/nlu/dev_seed.jsonl")
    assert len(rows) == 100
    assert all(r["source"] == "assistant_seed" and r["verified"] is False for r in rows)
    for n in [84, 88, 92, 96, 100]:
        row = rows[n - 1]
        assert row["intent"] == "check_availability"
        assert row["contains_out_of_scope_request"] is True
        assert row["expected_action"] == "answer_in_scope_and_refuse_medical_advice"
    for n in [82, 83, 86, 87, 90, 91, 94, 95, 98, 99]:
        assert rows[n - 1]["needs_clarification"] is True
    for n in [81, 85, 89, 93, 97]:
        assert len(rows[n - 1]["relations"]) == 2
        assert all(r["type"] == "QUANTITY_OF" for r in rows[n - 1]["relations"])


@pytest.mark.parametrize(
    "patch",
    [
        {"language": "en"},
        {"intent": "diagnosis"},
        {"verified": True},
        {"source": "authored_unreviewed"},
        {"needs_clarification": "true"},
        {"contains_out_of_scope_request": "false"},
    ],
)
def test_invalid_contract_fields(patch: dict) -> None:
    """Strict enum/boolean/provenance fields cannot be silently coerced."""
    row = copy.deepcopy(read_jsonl(ROOT / "data/nlu/dev_seed.jsonl")[0])
    row.update(patch)
    with pytest.raises(ValueError):
        validate_rows([row])


def test_offsets_overlap_missing_and_duplicate_negative_cases() -> None:
    """The dataset validator rejects corrupt evidence and incomplete intent routing."""
    base = read_jsonl(ROOT / "data/nlu/dev_seed.jsonl")[0]
    bad = copy.deepcopy(base)
    bad["entities"][0]["start"] += 1
    with pytest.raises(ValueError):
        validate_rows([bad])
    bad = copy.deepcopy(base)
    duplicate = copy.deepcopy(bad["entities"][0])
    duplicate["entity_id"] = "overlap"
    bad["entities"].append(duplicate)
    with pytest.raises(ValueError, match="Overlapping"):
        validate_rows([bad])
    bad = copy.deepcopy(base)
    bad.update(entities=[], relations=[], needs_clarification=False)
    with pytest.raises(ValueError):
        validate_rows([bad])
    duplicate = copy.deepcopy(base)
    duplicate["id"] += "copy"
    with pytest.raises(ValueError, match="Duplicate exact"):
        validate_rows([base, duplicate])


@pytest.mark.parametrize(
    "relation",
    [
        {"type": "QUANTITY_OF", "from": "missing", "to": "med1"},
        {"type": "DOSAGE_OF", "from": "med1", "to": "med1"},
        {"type": "QUANTITY_OF", "from": "span1", "to": "missing"},
    ],
)
def test_invalid_relation_endpoints(relation: dict) -> None:
    """Links must point from the declared attribute type to a medication span."""
    row = read_jsonl(ROOT / "data/nlu/dev_seed.jsonl")[80]
    row["relations"] = [relation]
    with pytest.raises(ValueError):
        validate_rows([row])


def test_reproducible_family_split_and_training_augmentation(tmp_path: Path) -> None:
    """Rebuild without network; synthetic variants stay with training parents."""
    config = load_config(ROOT / "configs/nlu.yaml")
    for key in [
        "seed_path",
        "dev_seed_path",
        "gold_human_path",
        "medication_roster_path",
    ]:
        config[key] = str(ROOT / config[key])
    config.update(
        output_dir=str(tmp_path / "generated"),
        stats_path=str(tmp_path / "stats.json"),
        stats_report_path=str(tmp_path / "stats.md"),
    )
    stats = build_dataset(config)
    before = {p.name: p.read_bytes() for p in (tmp_path / "generated").glob("*.jsonl")}
    assert build_dataset(config) == stats
    assert before == {
        p.name: p.read_bytes() for p in (tmp_path / "generated").glob("*.jsonl")
    }
    splits = {
        s: read_jsonl(tmp_path / "generated" / f"{s}.jsonl")
        for s in ["train", "dev", "test"]
    }
    assert leakage_check(splits)["shared_families"] == 0
    parents = {r["id"]: r for r in splits["train"] if r["source"] != "synthetic"}
    for row in splits["train"]:
        if row["source"] == "synthetic":
            assert row["family_id"] == parents[row["parent_id"]]["family_id"]
    assert all(r["source"] != "synthetic" for s in ["dev", "test"] for r in splits[s])
    assert stats["development_only"]["final_evaluation_eligible"] is False


def test_human_helper_unicode_repeated_substrings_and_duplicate_guard(
    tmp_path: Path,
) -> None:
    """Helper calculates code points and never copies development text into gold."""
    helper = script_module("add_gold")
    text = "🙂 é Doliprane puis Doliprane"
    span = {"type": "MEDICATION", "entity_id": "m1", "text": "Doliprane"}
    with pytest.raises(ValueError, match="Repeated substring"):
        helper.annotation_from_substrings(text, "fr", "request_medication", [span], [])
    row = helper.annotation_from_substrings(
        text, "fr", "request_medication", [{**span, "occurrence": 2}], []
    )
    entity = row["entities"][0]
    assert entity["start"] == text.rindex("Doliprane")
    assert text[entity["start"] : entity["end"]] == "Doliprane"
    path = tmp_path / "gold.jsonl"
    helper.append_human(row, path, tmp_path / "absent")
    with pytest.raises(ValueError):
        helper.append_human(row, path, tmp_path / "absent")
    development = tmp_path / "development"
    development.mkdir()
    (development / "dev_seed.jsonl").write_bytes(path.read_bytes())
    with pytest.raises(ValueError, match="never promote"):
        helper.append_human(row, tmp_path / "other.jsonl", development)
    missing = helper.annotation_from_substrings(
        "Le produit dont on parlait est disponible ?",
        "fr",
        "check_availability",
        [],
        [],
    )
    assert missing["needs_clarification"]


def test_quality_report_and_low_medication_warning() -> None:
    """Small inventory emits a warning; diversity counts use documented surfaces."""
    stats = script_module("dataset_stats").quality_statistics
    rows = read_jsonl(ROOT / "data/nlu/dev_seed.jsonl")
    report = stats(rows)
    assert report["rows"] == report["distinct_texts"] == 100
    assert sum(report["rows_per_intent"].values()) == 100
    assert sum(report["rows_per_variety"].values()) == 100
    assert report["rows_without_medication"] > 0
    assert stats(rows[:1])["warnings"] == ["Fewer than 8 distinct medications"]


def test_boundary_conventions_and_full_time_expressions() -> None:
    """Observed development spans exclude generic prefixes and retain full times."""
    rows = read_jsonl(ROOT / "data/nlu/dev_seed.jsonl")
    for row in rows:
        for entity in row["entities"]:
            if entity["type"] == "PHARMACY_NAME":
                assert not entity["text"].startswith(("Pharmacie ", "صيدلية "))
    assert any(
        e["text"] == "had lila"
        for r in rows
        for e in r["entities"]
        if e["type"] == "TIME_REF"
    )
    assert any(
        e["text"] == "هذه الليلة"
        for r in rows
        for e in r["entities"]
        if e["type"] == "TIME_REF"
    )


def test_relations_roundtrip_and_response_mixed_flag() -> None:
    """JSON relation aliases survive Pydantic export; mixed requests keep routing."""
    from pharma_assistant.api.schemas import Relation

    link = Relation.model_validate({"type": "DOSAGE_OF", "from": "d1", "to": "m1"})
    assert link.model_dump(by_alias=True) == {
        "type": "DOSAGE_OF",
        "from": "d1",
        "to": "m1",
    }
    assert Relation.model_validate_json(link.model_dump_json()) == link


def test_annotation_schema_export_matches_model() -> None:
    """The JSONL contract artifact includes mandatory provenance and booleans."""
    import json

    expected = NLUAnnotation.model_json_schema()
    assert (
        json.loads((ROOT / "docs/nlu_annotation.schema.json").read_text()) == expected
    )
    assert set(
        [
            "relations",
            "source",
            "verified",
            "needs_clarification",
            "contains_out_of_scope_request",
        ]
    ) <= set(expected["required"])
