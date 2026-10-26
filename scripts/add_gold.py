"""Append one explicitly verified human annotation, deriving Unicode span offsets."""

import argparse
import json
from pathlib import Path
from uuid import uuid4

from pharma_assistant.api.schemas import NLUAnnotation
from pharma_assistant.data_tools.nlu_dataset import read_jsonl, write_jsonl


def annotation_from_substrings(
    text: str,
    language: str,
    intent: str,
    spans: list[dict],
    relations: list[dict],
    *,
    needs_clarification: bool = False,
    contains_out_of_scope_request: bool = False,
) -> dict:
    """Use exact substrings; repeated occurrences require an explicit 1-based choice."""
    entities = []
    for specification in spans:
        entity = specification.copy()
        occurrence = entity.pop("occurrence", None)
        surface = entity["text"]
        if not surface:
            raise ValueError("Span substring must be nonblank")
        positions = [i for i in range(len(text)) if text.startswith(surface, i)]
        if not positions:
            raise ValueError(f"Substring absent from input: {surface!r}")
        if occurrence is None:
            if len(positions) != 1:
                raise ValueError("Repeated substring: supply a 1-based occurrence")
            occurrence = 1
        if type(occurrence) is not int or not 1 <= occurrence <= len(positions):
            raise ValueError("Invalid substring occurrence")
        start = positions[occurrence - 1]
        entity.update(start=start, end=start + len(surface))
        entities.append(entity)
    missing_medication = intent in {
        "check_availability",
        "request_medication",
        "price_inquiry",
    } and not any(
        e["type"] == "MEDICATION" and e.get("assertion", "affirmed") == "affirmed"
        for e in entities
    )
    identifier = f"human_{uuid4().hex}"
    row = {
        "id": identifier,
        "text": text,
        "language": language,
        "intent": intent,
        "entities": entities,
        "relations": relations,
        "needs_clarification": needs_clarification or missing_medication,
        "contains_out_of_scope_request": contains_out_of_scope_request,
        "source": "human",
        "verified": True,
        "family_id": identifier,
        "split": "gold_human",
    }
    NLUAnnotation.model_validate(row)
    return row


def append_human(row: dict, output: Path, development_dir: Path) -> None:
    """Reject duplicate text and copying development annotations into final gold."""
    existing = read_jsonl(output) if output.exists() else []
    for path in development_dir.rglob("*.jsonl"):
        if path.resolve() != output.resolve():
            if any(other["text"] == row["text"] for other in read_jsonl(path)):
                raise ValueError(
                    "Text already occurs in development data; never promote it to gold"
                )
    from pharma_assistant.data_tools.nlu_dataset import validate_rows

    for other in existing:
        if other["source"] != "human" or not other["verified"]:
            raise ValueError("Existing gold contains a non-human/unverified row")
    validate_rows(existing + [row])
    write_jsonl(output, existing + [row])


def main() -> None:
    """Accept annotations supplied by the human; never infer names or advice."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", required=True)
    parser.add_argument("--language", required=True)
    parser.add_argument("--intent", required=True)
    parser.add_argument("--span", action="append", type=json.loads, default=[])
    parser.add_argument("--relation", action="append", type=json.loads, default=[])
    parser.add_argument("--needs-clarification", action="store_true")
    parser.add_argument("--contains-out-of-scope-request", action="store_true")
    parser.add_argument(
        "--verified",
        action="store_true",
        required=True,
        help="Attest that you authored/collected and checked this annotation",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("data/nlu/gold_human.jsonl")
    )
    args = parser.parse_args()
    try:
        row = annotation_from_substrings(
            args.text,
            args.language,
            args.intent,
            args.span,
            args.relation,
            needs_clarification=args.needs_clarification,
            contains_out_of_scope_request=args.contains_out_of_scope_request,
        )
        append_human(row, args.output, Path("data/nlu"))
    except (ValueError, KeyError) as error:
        parser.error(str(error))
    print(f"Added one human annotation: {row['id']}")


if __name__ == "__main__":
    main()
