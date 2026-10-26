"""Propose draft annotations for human correction; never write final human gold."""

import argparse
import hashlib
import re
from collections.abc import Iterator
from pathlib import Path
from typing import get_args

from pharma_assistant.api.schemas import IntentLabel, Language
from pharma_assistant.data_tools.fetch_pharmacies import load_config
from pharma_assistant.data_tools.nlu_dataset import (
    read_jsonl,
    validate_rows,
    write_jsonl,
)

MED_INTENTS = {"check_availability", "request_medication", "price_inquiry"}
TYPE_IDS = {
    "MEDICATION": "m",
    "DOSAGE": "d",
    "FORM": "f",
    "QUANTITY": "q",
    "PHARMACY_NAME": "p",
    "LOCATION": "loc",
    "TIME_REF": "t",
    "URGENCY": "u",
}
NOTE_TAGS = {
    "needs_clarification",
    "mixed_oos",
    "multi_med",
    "typo",
    "urgent",
    "dosage",
    "form",
    "quantity",
    "pharmacy_name",
    "location",
    "time",
    "greeting",
    "check",
    "dosage_advice",
    "diagnosis",
    "unrelated",
    "substitution",
    "interaction_advice",
}


def parse_draft(path: Path) -> list[dict]:
    """Read columns; consume exactly one separator space, preserving message text."""
    records = []
    for number, raw in enumerate(path.read_bytes().decode("utf-8-sig").split("\n"), 1):
        line = raw.removesuffix("\r")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("|", 3)
        if len(parts) != 4:
            raise ValueError(f"Line {number}: expected four pipe-separated columns")
        language, intent, notes = (part.strip() for part in parts[:3])
        text = parts[3].removeprefix(" ")
        if language not in get_args(Language) or not intent or not text.strip():
            raise ValueError(f"Line {number}: invalid variety, empty intent or text")
        records.append(
            {
                "line_number": number,
                "language": language,
                "proposed_intent": intent,
                "notes": notes,
                "text": text,
            }
        )
    if not records:
        raise ValueError("Draft has no message rows")
    return records


def mention_matches(text: str, terms: list[str]) -> Iterator[re.Match[str]]:
    """Find exact case-insensitive mentions, excluding optional clitic prefixes."""
    alternatives = "|".join(
        re.escape(term) for term in sorted(terms, key=len, reverse=True)
    )
    pattern = rf"(?<!\w)(?:[وفبل]|[ld]['’])?(?P<mention>{alternatives})(?!\w)"
    return re.finditer(pattern, text, flags=re.IGNORECASE)


def propose(record: dict, config: dict, index: int) -> dict:
    """Use draft-specific lexicons and notes; all extracted fields are proposals."""
    text = record["text"]
    entities: list[dict] = []
    links: list[tuple[dict, dict]] = []
    warnings = []
    tags = set(filter(None, re.split(r"[, +]+", record["notes"].strip())))
    for unknown in sorted(tags - NOTE_TAGS):
        warnings.append(f"Unknown note tag: {unknown}; review manually")
    intent = config["intent_aliases"].get(
        record["proposed_intent"], record["proposed_intent"]
    )
    if intent not in get_args(IntentLabel):
        raise ValueError(f"Line {record['line_number']}: unknown intent {intent!r}")
    if intent != record["proposed_intent"]:
        warnings.append(
            f"Label typo proposed correction: {record['proposed_intent']} → {intent}"
        )

    def add(kind: str, start: int, end: int, **fields: object) -> dict | None:
        if any(start < e["end"] and e["start"] < end for e in entities):
            return None
        entity = {
            "type": kind,
            "text": text[start:end],
            "start": start,
            "end": end,
            **fields,
        }
        entities.append(entity)
        return entity

    for match in mention_matches(text, config["medications"]):
        add("MEDICATION", *match.span("mention"))
    medications = sorted(entities.copy(), key=lambda e: e["start"])
    for medication in medications:
        if medication["text"].casefold() in {
            s.casefold() for s in config["uncertain_mentions"]
        }:
            warnings.append(
                f"Unresolved name/spelling {medication['text']!r}; "
                "confirm intended product; no catalogue identity assigned"
            )
    if (
        intent == "greeting_smalltalk"
        and medications
        and re.search(r"\b(trouver|dispo|kayn)\b", text, re.I)
    ):
        intent = "check_availability"
        warnings.append(
            "Substantive medication-finding request overrides greeting; review intent"
        )

    # A unitless number after a medication is ambiguous strength, never inferred mg.
    strength = re.compile(
        r"\s*(?P<span>\d+(?:[.,]\d+)?(?:\s*(?P<unit>mg/mL|g/L|mcg|mg|g|ملغ|غ|%|IU))?)(?!\w)",
        re.I,
    )
    for medication in medications:
        match = strength.match(text, medication["end"])
        if match:
            raw_unit = match.group("unit")
            fields = {}
            if raw_unit:
                number = re.match(r"\d+(?:[.,]\d+)?", match.group("span")).group()
                units = {
                    "mg/ml": "mg/mL",
                    "g/l": "g/L",
                    "iu": "IU",
                    "غ": "g",
                    "ملغ": "mg",
                }
                fields = {
                    "value": float(number.replace(",", ".")),
                    "unit": units.get(raw_unit.lower(), raw_unit.lower()),
                }
            else:
                warnings.append(
                    f"Strength {match.group('span')!r} has no explicit unit; "
                    "do not infer one"
                )
            entity = add("DOSAGE", *match.span("span"), **fields)
            if entity is not None:
                links.append((entity, medication))

    packages = "|".join(
        re.escape(p) for p in sorted(config["packages"], key=len, reverse=True)
    )
    package_pattern = (
        rf"(?<!\w)[و]?(?P<span>(?P<n>[1-9]\d*)\s+(?P<package>{packages}))(?!\w)"
    )
    for match in re.finditer(package_pattern, text, re.I):
        add(
            "QUANTITY",
            *match.span("span"),
            value=int(match.group("n")),
            unit=config["packages"][match.group("package").lower()],
        )
    for match in mention_matches(text, ["علبتين", "علبتان"]):
        add("QUANTITY", *match.span("mention"), value=2, unit="box")
    for match in mention_matches(text, list(config["forms"])):
        add(
            "FORM",
            *match.span("mention"),
            normalized=config["forms"][match.group("mention").lower()],
        )

    # Bare explicit counts retain unit=unit; omitted packaging is never inherited.
    for match in re.finditer(r"(?<!\w)[و]?(?P<n>[1-9]\d*)(?!\w)", text):
        start, end = match.span("n")
        following = sorted(
            [
                e
                for e in entities
                if e["start"] >= end and e["type"] in {"MEDICATION", "FORM"}
            ],
            key=lambda e: e["start"],
        )
        if following and re.fullmatch(
            r"\s*(?:(?:dyal|de|d['’]|ديال|من)\s*)?",
            text[end : following[0]["start"]],
            re.I,
        ):
            entity = add(
                "QUANTITY", start, end, value=int(match.group("n")), unit="unit"
            )
            if entity:
                warnings.append(
                    f"Count {entity['text']!r} has no stated package unit; left as unit"
                )

    for kind, key in [
        ("PHARMACY_NAME", "pharmacy_names"),
        ("LOCATION", "locations"),
        ("TIME_REF", "times"),
        ("URGENCY", "urgency"),
    ]:
        terms = list(config[key])
        for match in mention_matches(text, terms):
            fields = {}
            if kind == "TIME_REF":
                fields["normalized"] = config[key][match.group("mention").lower()]
            if kind == "URGENCY":
                fields["normalized"] = "urgent"
            add(kind, *match.span("mention"), **fields)

    def connected(left: int, right: int) -> bool:
        # Ignore already extracted product attributes within the local noun phrase.
        fragments = []
        cursor = left
        for e in sorted(entities, key=lambda e: e["start"]):
            if (
                left <= e["start"]
                and e["end"] <= right
                and e["type"] in {"QUANTITY", "DOSAGE", "FORM"}
            ):
                fragments.append(text[cursor : e["start"]])
                cursor = e["end"]
        fragments.append(text[cursor:right])
        return (
            re.fullmatch(
                r"[\s]*(?:(?:dyal|de|d['’]|ديال|من|en)[\s]*)?", "".join(fragments), re.I
            )
            is not None
        )

    for entity in entities:
        if entity["type"] not in {"QUANTITY", "FORM"}:
            continue
        following = [
            m
            for m in medications
            if m["start"] >= entity["end"] and connected(entity["end"], m["start"])
        ]
        preceding = [
            m
            for m in medications
            if m["end"] <= entity["start"] and connected(m["end"], entity["start"])
        ]
        if len(following) == 1:
            links.append((entity, following[0]))
        elif not following and len(preceding) == 1:
            links.append((entity, preceding[0]))
        else:
            warnings.append(
                f"Unresolved {entity['type']} association for {entity['text']!r}"
            )

    entities.sort(key=lambda e: e["start"])
    counters: dict[str, int] = {}
    for entity in entities:
        kind = entity["type"]
        counters[kind] = counters.get(kind, 0) + 1
        entity["entity_id"] = TYPE_IDS[kind] + str(counters[kind])
    relations = []
    for entity, medication in links:
        entity["medication_ref"] = medication["entity_id"]
        if entity["type"] in {"QUANTITY", "DOSAGE"}:
            relations.append(
                {
                    "type": entity["type"] + "_OF",
                    "from": entity["entity_id"],
                    "to": medication["entity_id"],
                }
            )
    relations.sort(key=lambda r: r["from"])
    missing_med = intent in MED_INTENTS and not medications
    ambiguous = any(e["type"] == "DOSAGE" and e.get("value") is None for e in entities)
    unlinked = any(
        e["type"] in {"DOSAGE", "FORM", "QUANTITY"} and not e.get("medication_ref")
        for e in entities
    )
    missing_directory = intent.startswith("pharmacy_info_") and not any(
        e["type"] in {"LOCATION", "PHARMACY_NAME"} for e in entities
    )
    clarify = "needs_clarification" in tags or missing_med or missing_directory
    if intent != "out_of_scope":
        clarify = clarify or ambiguous or (bool(medications) and unlinked)
    if missing_med:
        warnings.append(
            "No named medication; request clarification without guessing a product"
        )
    for tag, kind in [
        ("form", "FORM"),
        ("quantity", "QUANTITY"),
        ("dosage", "DOSAGE"),
        ("multi_med", "MEDICATION"),
        ("pharmacy_name", "PHARMACY_NAME"),
        ("location", "LOCATION"),
        ("time", "TIME_REF"),
        ("urgent", "URGENCY"),
    ]:
        count = sum(e["type"] == kind for e in entities)
        if count < (2 if tag == "multi_med" else 1) and tag in tags:
            warnings.append(
                f"Note {tag!r} not fully supported by explicit spans; "
                "do not invent evidence"
            )
    if "mixed_oos" in tags:
        warnings.append(
            "Handle only the in-scope request; refuse medical-advice clause. "
            "Medication mentions there are evidence, not extra stock requests"
        )
    return {
        "id": f"draft_review_{index:03d}",
        "text": text,
        "language": record["language"],
        "intent": intent,
        "entities": entities,
        "relations": relations,
        "needs_clarification": bool(clarify),
        "contains_out_of_scope_request": "mixed_oos" in tags,
        "source": "assistant_seed",
        "verified": False,
        "family_id": f"draft_review/{index:03d}",
        "split": "review_only",
        "review_status": "pending_human_correction",
        "authoring_method": "assistant_draft_span_proposal",
        "draft": {
            "line_number": record["line_number"],
            "proposed_intent": record["proposed_intent"],
            "notes": record["notes"],
            "review_notes": warnings,
            "duplicate_of": [],
        },
    }


def review_table(rows: list[dict]) -> str:
    """Render every proposed span with exact offsets, links and outstanding issues."""

    def escape(value: str) -> str:
        return value.replace("|", "\\|").replace("\r", "\\r").replace("\n", "\\n")

    lines = [
        "# Draft annotation proposals — NOT verified gold",
        "",
        "Every row is source=assistant_seed, verified=false, split=review_only.",
        "No message is rewritten. Correct JSONL annotations manually; "
        "do not promote assistant-authored messages to human gold.",
        "",
        "| Row / source line | Variety | Proposed intent | Original message | "
        "Proposed spans [start:end] | Relations | Clarify / mixed OOS | Review notes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        descriptions = []
        for entity in row["entities"]:
            details = [
                f"{key}={entity[key]}"
                for key in ["value", "unit", "normalized", "medication_ref"]
                if entity.get(key) is not None
            ]
            description = (
                f"{entity['entity_id']} {entity['type']} `{entity['text']}` "
                f"[{entity['start']}:{entity['end']}]"
            )
            if details:
                description += " (" + ", ".join(details) + ")"
            descriptions.append(description)
        spans = "; ".join(descriptions) or "—"
        links = (
            "; ".join(f"{r['type']} {r['from']} → {r['to']}" for r in row["relations"])
            or "—"
        )
        notes = "; ".join(row["draft"]["review_notes"])
        if row["draft"]["duplicate_of"]:
            notes += (
                ("; " if notes else "")
                + "DUPLICATE of "
                + ", ".join(row["draft"]["duplicate_of"])
            )
        cells = [
            f"{row['id']} / {row['draft']['line_number']}",
            row["language"],
            row["intent"],
            row["text"],
            spans,
            links,
            f"{row['needs_clarification']} / {row['contains_out_of_scope_request']}",
            notes,
        ]
        lines.append("| " + " | ".join(escape(c) for c in cells) + " |")
    return "\n".join(lines) + "\n"


def import_draft(config: dict, *, overwrite: bool = False) -> list[dict]:
    """Validate proposals before writing; protect final gold and corrected output."""
    source, output, report, gold = (
        Path(config[k])
        for k in ["input_path", "output_path", "report_path", "protected_gold_path"]
    )
    for destination in [output, report]:
        same_file = any(
            destination.exists()
            and protected.exists()
            and destination.samefile(protected)
            for protected in [gold, source]
        )
        if (
            same_file
            or destination.name == "gold_human.jsonl"
            or destination.resolve()
            in {
                gold.resolve(),
                source.resolve(),
            }
        ):
            raise ValueError("Refusing to overwrite final human gold or draft input")
        if destination.exists() and not overwrite:
            raise ValueError(
                "Review output exists; use --overwrite only to discard "
                "proposals/corrections"
            )
    if output.resolve() == report.resolve():
        raise ValueError("JSONL and review table destinations must differ")
    gold_before = gold.read_bytes() if gold.exists() else None
    rows = [
        propose(record, config, i) for i, record in enumerate(parse_draft(source), 1)
    ]
    existing: dict[str, list[str]] = {}
    for path in sorted(Path(config["dataset_dir"]).rglob("*.jsonl")):
        if path.resolve() == output.resolve():
            continue
        for other in read_jsonl(path):
            existing.setdefault(other["text"], []).append(
                f"{path.as_posix()}:{other['id']}"
            )
    for row in rows:
        row["draft"]["duplicate_of"] = existing.get(row["text"], [])
    validate_rows(rows)
    write_jsonl(output, rows)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(review_table(rows), encoding="utf-8")
    assert (gold.read_bytes() if gold.exists() else None) == gold_before
    return rows


def main() -> None:
    """Print the complete review table and save only unverified annotation proposals."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/gold_draft.yaml"))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--overwrite", action="store_true")
    mode.add_argument(
        "--print-existing",
        action="store_true",
        help="Validate and print corrected JSONL without writing any files",
    )
    args = parser.parse_args()
    config = load_config(args.config)
    try:
        if args.print_existing:
            rows = read_jsonl(Path(config["output_path"]))
            validate_rows(rows)
            original = parse_draft(Path(config["input_path"]))
            if [r["text"] for r in rows] != [r["text"] for r in original]:
                raise ValueError("Review rows must preserve all source texts in order")
            if any(
                r["verified"]
                or r["source"] != "assistant_seed"
                or r["split"] != "review_only"
                or not r.get("draft")
                for r in rows
            ):
                raise ValueError("Review proposals must stay unverified assistant rows")
        else:
            rows = import_draft(config, overwrite=args.overwrite)
    except (ValueError, KeyError) as error:
        parser.error(str(error))
    print(review_table(rows), end="")
    print(
        f"\nProposed {len(rows)} rows; all verified=false. gold_human.jsonl untouched."
    )
    print(
        "Review JSONL SHA-256: "
        + hashlib.sha256(Path(config["output_path"]).read_bytes()).hexdigest()
    )


if __name__ == "__main__":
    main()
