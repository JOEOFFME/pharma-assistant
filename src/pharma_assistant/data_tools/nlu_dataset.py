"""Deterministic NLU dataset preparation with auditable families and provenance."""

import copy
import hashlib
import json
import logging
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from pharma_assistant.api.schemas import AnalysisResponse
from pharma_assistant.data_tools.medication_names import latin_to_arabic

logger = logging.getLogger(__name__)
SPLITS = ("train", "dev", "test")
OPTIONAL_ATTRIBUTES = {"DOSAGE", "FORM", "QUANTITY", "TIME_REF", "URGENCY"}


def canonical(value: Any) -> str:
    """Serialize deterministically without rewriting Unicode source text."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    """Hash a canonical record, binding review to its complete annotations."""
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    """Read every nonblank line as one annotation record."""
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    """Write reproducible, inspectable JSONL with a final newline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(canonical(row) + "\n" for row in rows), encoding="utf-8")


def normalize_text(text: str) -> str:
    """Fingerprint punctuation/case/diacritic variants without changing annotations."""
    text = unicodedata.normalize("NFKD", text).casefold().replace("ـ", "")
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي"}))
    return " ".join("".join(char if char.isalnum() else " " for char in text).split())


def template_signature(row: dict) -> str:
    """Mask names and remove optional attributes to catch simple template leakage."""
    parts = []
    cursor = 0
    for entity in sorted(row["entities"], key=lambda item: item["start"]):
        parts.append(row["text"][cursor : entity["start"]])
        parts.append("" if entity["type"] in OPTIONAL_ATTRIBUTES else entity["type"])
        cursor = entity["end"]
    parts.append(row["text"][cursor:])
    return normalize_text(" ".join(parts))


def validate_rows(rows: list[dict]) -> None:
    """Validate IDs, provenance, raw spans and the response contract."""
    if len({row["id"] for row in rows}) != len(rows):
        raise ValueError("Duplicate example IDs")
    for row in rows:
        if row["source"] not in {"authored_unreviewed", "synthetic", "llm"}:
            raise ValueError("Missing/unsupported creation provenance")
        if row["source"] == "synthetic" and not row.get("parent_id"):
            raise ValueError("Synthetic examples require a parent")
        if not row.get("family_id"):
            raise ValueError("Every example needs a template family")
        for entity in row["entities"]:
            if row["text"][entity["start"] : entity["end"]] != entity["text"]:
                raise ValueError(f"Bad raw-text offsets in {row['id']}")
        info_type = {
            "pharmacy_info_phone": "phone",
            "pharmacy_info_location": "location",
            "pharmacy_info_hours": "hours",
        }.get(row["intent"])
        AnalysisResponse.model_validate(
            {
                "request_id": "00000000-0000-4000-8000-000000000001",
                "input": {
                    "modality": "text",
                    "raw_text": row["text"],
                    "language": row["language"],
                },
                "intent": {"label": row["intent"], "confidence": 0.5},
                "entities": row["entities"],
                "pharmacy_query": {
                    "needs_pharmacy_info": info_type is not None,
                    "info_type": info_type,
                },
                "needs_clarification": row["needs_clarification"],
                "clarification_question": {
                    "fr": (
                        "Pouvez-vous préciser ?" if row["needs_clarification"] else None
                    )
                },
                "latency_ms": 0,
            }
        )


def assign_families(seeds: list[dict], seed: int) -> dict[str, list[dict]]:
    """Group translations and exact delexicalized collisions before splitting."""
    parents = {row["family_id"]: row["family_id"] for row in seeds}

    def root(key: str) -> str:
        while parents[key] != key:
            key = parents[key]
        return key

    signatures: dict[str, str] = {}
    for row in seeds:
        signature = template_signature(row)
        family = row["family_id"]
        if signature in signatures:
            left, right = root(family), root(signatures[signature])
            if left != right:
                parents[max(left, right)] = min(left, right)
        else:
            signatures[signature] = family
    grouped: dict[str, list[dict]] = defaultdict(list)
    for source in seeds:
        row = copy.deepcopy(source)
        row["family_id"] = root(row["family_id"])
        grouped[row["family_id"]].append(row)
    by_intent: dict[str, list[str]] = defaultdict(list)
    for family, rows in grouped.items():
        intents = {row["intent"] for row in rows}
        if len(intents) != 1:
            raise ValueError("Template group mixes intents")
        by_intent[next(iter(intents))].append(family)
    result: dict[str, list[dict]] = {split: [] for split in SPLITS}
    for intent, families in sorted(by_intent.items()):
        if len(families) < 3:
            raise ValueError(f"Need three independent template groups for {intent}")
        families.sort(
            key=lambda family: hashlib.sha256(f"{seed}:{family}".encode()).hexdigest()
        )
        for index, family in enumerate(families):
            split = (
                "test"
                if index == len(families) - 1
                else "dev" if index == len(families) - 2 else "train"
            )
            for row in grouped[family]:
                row["split"] = split
                result[split].append(row)
    for rows in result.values():
        rows.sort(key=lambda row: row["id"])
    return result


def quantity_text(value: int, language: str, original: str) -> str:
    """Generate package-count wording, explicitly subject to native-speaker review."""
    if language in {"darija_ar", "ar"} or any(
        "\u0600" <= char <= "\u06ff" for char in original
    ):
        if value == 1:
            return "علبة"
        if value == 2:
            return "جوج علب" if language == "darija_ar" else "علبتين"
        return f"{value} علب"
    return f"{value} " + ("boîte" if value == 1 else "boîtes")


def augment(row: dict, medication: dict, quantity: int, mode: str, index: int) -> dict:
    """Replace spans and recompute offsets without inventing ingredient facts."""
    output = copy.deepcopy(row)
    fragments = []
    entities = []
    cursor = 0
    offset = 0
    for original in sorted(row["entities"], key=lambda entity: entity["start"]):
        prefix = row["text"][cursor : original["start"]]
        fragments.append(prefix)
        offset += len(prefix)
        entity = copy.deepcopy(original)
        surface = entity["text"]
        if entity["type"] == "MEDICATION":
            surface = medication["brand_name"]
            if row["language"] in {"darija_ar", "ar"}:
                surface = latin_to_arabic(surface)
            if mode == "noise":
                # Lexical Arabizi/noise only; strengths are never digit-mapped.
                surface = surface.lower()
                if row["language"] == "darija_latn":
                    surface = (
                        surface.replace("a", "3").replace("h", "7").replace("q", "9")
                    )
                elif len(surface) > 5:
                    surface = (
                        surface[: len(surface) // 2] + surface[len(surface) // 2 + 1 :]
                    )
        elif entity["type"] == "DOSAGE":
            surface = medication["strength_text"]
            entity["value"] = medication["strength_value"]
            entity["unit"] = medication["strength_unit"]
        elif entity["type"] == "QUANTITY":
            surface = quantity_text(quantity, row["language"], surface)
            entity["value"] = quantity
        entity.update(text=surface, start=offset, end=offset + len(surface))
        fragments.append(surface)
        entities.append(entity)
        offset += len(surface)
        cursor = original["end"]
    fragments.append(row["text"][cursor:])
    output.update(
        id=f"synthetic_{index:06d}",
        text="".join(fragments),
        entities=entities,
        source="synthetic",
        parent_id=row["id"],
        review_status="pending_native_speaker_review",
        augmentation={
            "medication_id": medication["id"],
            "reference_country": "FR",
            "quantity": quantity,
            "spelling_mode": mode,
            "note": "Authored request text; no stock or Moroccan market claim",
        },
    )
    return output


def leakage_check(splits: dict[str, list[dict]]) -> dict[str, int]:
    """Reject shared families, normalized text and template signatures."""
    indexes: dict[str, dict[str, str]] = {
        "family_id": {},
        "normalized_text": {},
        "template_signature": {},
    }
    for split, rows in splits.items():
        validate_rows(rows)
        for row in rows:
            fingerprints = {
                "family_id": row["family_id"],
                "normalized_text": normalize_text(row["text"]),
                "template_signature": template_signature(row),
            }
            for kind, value in fingerprints.items():
                previous = indexes[kind].get(value)
                if previous is not None and previous != split:
                    raise ValueError(
                        f"Leakage: {kind} shared by {previous} and {split}: {row['id']}"
                    )
                indexes[kind][value] = split
    return {
        "shared_families": 0,
        "shared_normalized_texts": 0,
        "shared_template_signatures": 0,
    }


def length_summary(rows: list[dict]) -> dict[str, int]:
    """Use floor(p*(n-1)) quantiles of Unicode code-point lengths."""
    lengths = sorted(len(row["text"]) for row in rows)
    if not lengths:
        return {"min": 0, "p50": 0, "p95": 0, "max": 0}
    return {
        "min": lengths[0],
        "p50": lengths[(len(lengths) - 1) // 2],
        "p95": lengths[int((len(lengths) - 1) * 0.95)],
        "max": lengths[-1],
    }


def dataset_statistics(splits: dict[str, list[dict]], gold: list[dict]) -> dict:
    """Report counts/lengths; pending gold candidates are not an evaluation set."""
    return {
        "splits": {
            split: {
                "rows": len(rows),
                "families": len({row["family_id"] for row in rows}),
                "intents": dict(sorted(Counter(row["intent"] for row in rows).items())),
                "languages": dict(
                    sorted(Counter(row["language"] for row in rows).items())
                ),
                "sources": dict(sorted(Counter(row["source"] for row in rows).items())),
                "length_codepoints": length_summary(rows),
                "sha256": hashlib.sha256(
                    "".join(canonical(row) + "\n" for row in rows).encode()
                ).hexdigest(),
            }
            for split, rows in splits.items()
        },
        "leakage": leakage_check({**splits, "gold_candidates": gold}),
        "gold": {
            "candidate_rows": len(gold),
            "verified_rows": 0,
            "status": "pending_human_review_not_locked",
            "intents": dict(sorted(Counter(row["intent"] for row in gold).items())),
            "languages": dict(sorted(Counter(row["language"] for row in gold).items())),
        },
    }


def write_statistics(stats: dict, path: Path, report: Path) -> None:
    """Save machine-readable counts and a plain-language coverage report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# NLU dataset statistics - TASK 5",
        "",
        "Assistant-authored seed and candidate examples remain unreviewed.",
        "Generated variants are flagged synthetic; no medical facts are invented.",
        "",
        "| Split | Rows | Template families |",
        "| --- | ---: | ---: |",
    ]
    for split, summary in stats["splits"].items():
        lines.append(f"| {split} | {summary['rows']} | {summary['families']} |")
    for field in ("intents", "languages", "sources"):
        lines += [
            "",
            f"## Counts by {field}",
            "",
            "| Split | Label | Count |",
            "| --- | --- | ---: |",
        ]
        for split, summary in stats["splits"].items():
            lines += [
                f"| {split} | {label} | {count} |"
                for label, count in summary[field].items()
            ]
    lines += [
        "",
        "## Unicode length distribution",
        "",
        "| Split | Min | P50 | P95 | Max |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for split, summary in stats["splits"].items():
        length = summary["length_codepoints"]
        lines.append(
            f"| {split} | {length['min']} | {length['p50']} | "
            f"{length['p95']} | {length['max']} |"
        )
    lines += [
        "",
        "## Held-out candidate status",
        "",
        f"Gold candidates: {stats['gold']['candidate_rows']}.",
        f"Human-verified gold: {stats['gold']['verified_rows']}.",
        "No gold test file is admitted or locked until per-record human review.",
        "Family, normalized-text and template-signature leakage checks passed.",
        "Semantic paraphrase leakage still requires human review.",
        "",
        "Rebuild: make dataset. See [instructions](../data/nlu/README.md).",
        "Machine-readable counts and split hashes: [nlu_stats.json](nlu_stats.json).",
    ]
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_dataset(config: dict) -> dict:
    """Prepare family-disjoint splits; augment training seeds only."""
    seeds = read_jsonl(Path(config["seed_path"]))
    gold = read_jsonl(Path(config["gold_candidates_path"]))
    validate_rows(seeds)
    validate_rows(gold)
    if len(seeds) < 150 or len(gold) < 100:
        raise ValueError("Require at least 150 seed rows and 100 gold candidates")
    splits = assign_families(seeds, int(config["seed"]))
    roster = json.loads(Path(config["medication_roster_path"]).read_text())
    roster = roster[: int(config["medication_limit"])]
    if not roster:
        raise ValueError("Medication roster is empty")
    generated = []
    for row in list(splits["train"]):
        if not any(entity["type"] == "MEDICATION" for entity in row["entities"]):
            continue
        for medication in roster:
            for quantity in config["quantities"]:
                for mode in config["spelling_modes"]:
                    generated.append(
                        augment(row, medication, quantity, mode, len(generated) + 1)
                    )
    # Deduplicate within each split; cross-split collisions remain errors.
    splits["train"].extend(generated)
    for split, rows in splits.items():
        seen = set()
        unique = []
        for row in rows:
            fingerprint = normalize_text(row["text"])
            if fingerprint not in seen:
                unique.append(row)
                seen.add(fingerprint)
        splits[split] = sorted(unique, key=lambda row: row["id"])
    stats = dataset_statistics(splits, gold)
    gold_path = Path(config["gold_test_path"])
    lock_path = Path(config["gold_lock_path"])
    if gold_path.exists() or lock_path.exists():
        from pharma_assistant.data_tools.gold_review import load_locked_gold

        admitted = load_locked_gold(gold_path, lock_path)
        leakage_check({**splits, "gold": admitted})
        stats["gold"]["verified_rows"] = len(admitted)
        stats["gold"]["status"] = "human_review_declared_locked"
    for split, rows in splits.items():
        write_jsonl(Path(config["output_dir"]) / f"{split}.jsonl", rows)
    write_statistics(
        stats, Path(config["stats_path"]), Path(config["stats_report_path"])
    )
    logger.info(
        "Built NLU splits: %s", {split: len(rows) for split, rows in splits.items()}
    )
    logger.info("Gold remains pending human review: %s candidates", len(gold))
    return stats
