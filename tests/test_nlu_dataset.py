"""Dataset/review controls; simulated test approvals never modify production gold."""

import copy
import json
from pathlib import Path

import pytest

from pharma_assistant.data_tools.fetch_pharmacies import load_config
from pharma_assistant.data_tools.gold_review import load_locked_gold, lock_gold
from pharma_assistant.data_tools.nlu_dataset import (
    assign_families,
    augment,
    build_dataset,
    digest,
    leakage_check,
    read_jsonl,
    validate_rows,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def prepared(tmp_path_factory: pytest.TempPathFactory) -> tuple:
    """Build from committed inputs in a temporary directory without network access."""
    config = load_config(ROOT / "configs/nlu.yaml")
    target = tmp_path_factory.mktemp("nlu")
    for key in (
        "seed_path",
        "gold_candidates_path",
        "gold_review_path",
        "medication_roster_path",
    ):
        config[key] = str(ROOT / config[key])
    config.update(
        output_dir=str(target / "generated"),
        stats_path=str(target / "stats.json"),
        stats_report_path=str(target / "report.md"),
        gold_test_path=str(target / "gold.jsonl"),
        gold_lock_path=str(target / "gold.lock.json"),
    )
    stats = build_dataset(config)
    splits = {
        split: read_jsonl(Path(config["output_dir"]) / f"{split}.jsonl")
        for split in ("train", "dev", "test")
    }
    return config, stats, splits, target


def test_seed_and_candidate_coverage() -> None:
    """Seed/candidate counts, varieties and creation provenance remain explicit."""
    seeds = read_jsonl(ROOT / "data/nlu/seed.jsonl")
    gold = read_jsonl(ROOT / "data/nlu/gold_candidates.jsonl")
    assert len(seeds) == 200 and len(gold) == 100
    validate_rows(seeds)
    validate_rows(gold)
    assert len({row["intent"] for row in seeds}) == 8
    assert len({row["language"] for row in seeds}) == 5
    assert len({row["intent"] for row in gold}) == 8
    assert all(row["source"] == "authored_unreviewed" for row in seeds + gold)
    assert all(row["review_status"] == "pending_native_speaker_review" for row in gold)


def test_review_template_hashes_match_all_annotations() -> None:
    """Reviews cannot apply to an older text or differently annotated record."""
    rows = read_jsonl(ROOT / "data/nlu/gold_candidates.jsonl")
    review = json.loads((ROOT / "data/nlu/gold_review.json").read_text())
    by_id = {item["id"]: item for item in review["rows"]}
    assert len(by_id) == 100
    for row in rows:
        assert by_id[row["id"]]["example_sha256"] == digest(row)
        assert isinstance(by_id[row["id"]]["approved"], bool)


def test_training_only_augmentation_and_family_separation(prepared: tuple) -> None:
    """Descendants stay in their training parent's family and split."""
    _, stats, splits, _ = prepared
    parents = {
        row["id"]: row for row in splits["train"] if row["source"] != "synthetic"
    }
    generated = [row for row in splits["train"] if row["source"] == "synthetic"]
    assert generated
    for row in generated:
        assert row["parent_id"] in parents
        assert row["family_id"] == parents[row["parent_id"]]["family_id"]
        assert row["augmentation"]["reference_country"] == "FR"
    assert all(
        row["source"] != "synthetic"
        for split in ("dev", "test")
        for row in splits[split]
    )
    assert stats["leakage"] == {
        "shared_families": 0,
        "shared_normalized_texts": 0,
        "shared_template_signatures": 0,
    }
    for rows in splits.values():
        assert len({row["intent"] for row in rows}) == 8
        assert len({row["language"] for row in rows}) == 5


@pytest.mark.parametrize("change_family", [False, True])
def test_leakage_is_not_silently_dropped(prepared: tuple, change_family: bool) -> None:
    """Shared text cannot be hidden by renaming its family or record ID."""
    source = copy.deepcopy(prepared[2]["train"][0])
    other = copy.deepcopy(source)
    other["id"] += "_other"
    if change_family:
        other["family_id"] += "_other"
    with pytest.raises(ValueError, match="Leakage"):
        leakage_check({"train": [source], "test": [other]})


def test_optional_attribute_template_collisions_are_grouped() -> None:
    """Adding strength text must not split one basic phrase across train/test."""
    rows = read_jsonl(ROOT / "data/nlu/seed.jsonl")
    splits = assign_families(rows, 42)
    assert leakage_check(splits)["shared_template_signatures"] == 0
    placement = {
        row["source_example_id"]: (split, row["family_id"])
        for split, examples in splits.items()
        for row in examples
    }
    assert (
        placement["check_availability.fr.01"] == placement["check_availability.fr.04"]
    )
    assert placement["price_inquiry.fr.01"] == placement["price_inquiry.fr.04"]


def test_unicode_spans_recomputed_after_augmentation() -> None:
    """Emoji/code-point prefixes must not shift offsets as UTF-16 bytes would."""
    text = "🙂 بغيت Doliprane 500 mg"
    med = text.index("Doliprane")
    strength = text.index("500 mg")
    row = {
        "id": "fixture",
        "text": text,
        "intent": "request_medication",
        "language": "mixed",
        "family_id": "fixture",
        "split": "train",
        "source": "authored_unreviewed",
        "needs_clarification": False,
        "entities": [
            {"type": "MEDICATION", "text": "Doliprane", "start": med, "end": med + 9},
            {
                "type": "DOSAGE",
                "text": "500 mg",
                "start": strength,
                "end": strength + 6,
                "value": 500,
                "unit": "mg",
            },
        ],
    }
    roster = json.loads((ROOT / "data/nlu/medication_roster.json").read_text())
    changed = augment(row, roster[0], 3, "noise", 1)
    validate_rows([changed])
    assert changed["text"].startswith("🙂")
    assert changed["source"] == "synthetic"


def test_build_is_deterministic(prepared: tuple) -> None:
    """Rebuilding uses no random APIs, provider calls or review mutation."""
    config, stats, _, _ = prepared
    before = {
        split: (Path(config["output_dir"]) / f"{split}.jsonl").read_bytes()
        for split in ("train", "dev", "test")
    }
    assert build_dataset(config) == stats
    assert all(
        (Path(config["output_dir"]) / f"{split}.jsonl").read_bytes() == content
        for split, content in before.items()
    )


def test_pending_review_cannot_be_locked(tmp_path: Path) -> None:
    """No production example is labelled human-verified by a build command."""
    output, seal = tmp_path / "gold.jsonl", tmp_path / "gold.lock.json"
    document = json.loads((ROOT / "data/nlu/gold_review.json").read_text())
    document["rows"][0]["approved"] = False
    review_path = tmp_path / "pending_review.json"
    review_path.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="Human review missing"):
        lock_gold(
            ROOT / "data/nlu/gold_candidates.jsonl",
            review_path,
            output,
            seal,
        )
    assert not output.exists() and not seal.exists()


def simulated_reviews() -> dict:
    """Use conspicuous test-only review metadata, never actual human approval."""
    document = json.loads((ROOT / "data/nlu/gold_review.json").read_text())
    for review in document["rows"]:
        review.update(
            approved=True,
            reviewed_by="UNIT_TEST_SIMULATED_REVIEW",
            reviewed_at="2000-01-01T00:00:00+00:00",
        )
    return document


def test_stale_review_is_rejected(tmp_path: Path) -> None:
    """A prior review cannot silently approve a changed record."""
    review = simulated_reviews()
    review["rows"][0]["example_sha256"] = "0" * 64
    path = tmp_path / "review.json"
    path.write_text(json.dumps(review))
    with pytest.raises(ValueError, match="Review hash mismatch"):
        lock_gold(
            ROOT / "data/nlu/gold_candidates.jsonl",
            path,
            tmp_path / "gold.jsonl",
            tmp_path / "gold.lock.json",
        )


def test_lock_integrity_and_no_overwrite(tmp_path: Path) -> None:
    """Exercise sealing with simulated test approvals, then reject tampering."""
    review_path = tmp_path / "review.json"
    review_path.write_text(json.dumps(simulated_reviews()))
    output, seal = tmp_path / "gold.jsonl", tmp_path / "gold.lock.json"
    candidates = ROOT / "data/nlu/gold_candidates.jsonl"
    lock_gold(candidates, review_path, output, seal)
    assert len(load_locked_gold(output, seal)) == 100
    with pytest.raises(ValueError, match="immutable"):
        lock_gold(candidates, review_path, output, seal)
    output.write_bytes(output.read_bytes() + b" ")
    with pytest.raises(ValueError, match="Gold hash mismatch"):
        load_locked_gold(output, seal)


def test_invalid_source_or_offsets_are_rejected() -> None:
    """Annotation validation checks source provenance and verbatim spans."""
    row = read_jsonl(ROOT / "data/nlu/seed.jsonl")[0]
    row["source"] = "invented_human_gold"
    with pytest.raises(ValueError):
        validate_rows([row])
    row["source"] = "authored_unreviewed"
    row["entities"][0]["start"] += 1
    with pytest.raises(ValueError, match="offset"):
        validate_rows([row])
