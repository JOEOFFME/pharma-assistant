"""Rebuild NLU splits and print auditable quality counts for every JSONL file."""

import argparse
import json
import logging
from collections import Counter
from pathlib import Path

from pharma_assistant.data_tools.fetch_pharmacies import load_config
from pharma_assistant.data_tools.nlu_dataset import (
    build_dataset,
    normalize_text,
    read_jsonl,
)


def quality_statistics(rows: list[dict]) -> dict:
    """Count distinct medication surface forms, without claiming resolved identities."""
    medications = {
        normalize_text(entity["text"])
        for row in rows
        for entity in row["entities"]
        if entity["type"] == "MEDICATION"
    }
    return {
        "rows": len(rows),
        "rows_per_intent": dict(sorted(Counter(r["intent"] for r in rows).items())),
        "rows_per_variety": dict(sorted(Counter(r["language"] for r in rows).items())),
        "distinct_texts": len({r["text"] for r in rows}),
        "distinct_medications": len(medications),
        "medication_count_basis": (
            "case/accent-normalized surface forms; "
            "aliases/noise may inflate identities"
        ),
        "rows_without_medication": sum(
            not any(e["type"] == "MEDICATION" for e in r["entities"]) for r in rows
        ),
        "warnings": (
            ["Fewer than 8 distinct medications"] if len(medications) < 8 else []
        ),
    }


def main() -> None:
    """Rebuild reproducibly, then report each file and the union without promotion."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/nlu.yaml"))
    args = parser.parse_args()
    config = load_config(args.config)
    build_dataset(config)
    paths = sorted(Path("data/nlu").rglob("*.jsonl"))
    files = {str(path): quality_statistics(read_jsonl(path)) for path in paths}
    all_rows = [row for path in paths for row in read_jsonl(path)]
    report = {"files": files, "all_files": quality_statistics(all_rows)}
    Path("docs/nlu_quality.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    for path, summary in files.items():
        for warning in summary["warnings"]:
            print(f"WARNING [{path}]: {warning}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
