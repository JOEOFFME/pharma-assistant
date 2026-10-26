"""Evaluate authored review queries, not a validated clinical benchmark."""

import argparse
import hashlib
import json
import logging
from pathlib import Path

from pharma_assistant.data_tools.fetch_pharmacies import load_config
from pharma_assistant.matching.medications import MedicationIndex

logger = logging.getLogger(__name__)


def evaluate(config: dict) -> dict:
    """Save candidate lists so each top-k accuracy count can be recomputed."""
    path = Path(config["queries_path"])
    queries = json.loads(path.read_text(encoding="utf-8"))
    if len(queries) != 50 or len({row["id"] for row in queries}) != 50:
        raise ValueError("Expected exactly 50 uniquely identified review queries")
    index = MedicationIndex.from_database(
        Path(config["database_path"]), config["matching"]
    )
    predictions = []
    for row in queries:
        expected = set(row["expected_ids"])
        if not expected or not expected.issubset(index.records):
            raise ValueError("Expected IDs must exist in the pinned source catalogue")
        hits = index.search(row["query"], k=3)
        ids = [hit.medication.id for hit in hits]
        predictions.append(
            {
                "id": row["id"],
                "query": row["query"],
                "expected_ids": row["expected_ids"],
                "underspecified": row["underspecified"],
                "top1_correct": bool(ids and ids[0] in expected),
                "top3_correct": bool(set(ids) & expected),
                "candidates": [
                    {
                        "id": hit.medication.id,
                        "full_name": hit.medication.full_name,
                        "score": hit.score,
                        "needs_clarification": hit.needs_clarification,
                    }
                    for hit in hits
                ],
            }
        )
    count = len(predictions)
    summary = {
        "queries": count,
        "top1_correct": sum(r["top1_correct"] for r in predictions),
        "top3_correct": sum(r["top3_correct"] for r in predictions),
        "underspecified_queries": sum(r["underspecified"] for r in predictions),
        "review_status": "authored_unreviewed_not_gold",
    }
    summary["top1_accuracy"] = round(summary["top1_correct"] / count, 6)
    summary["top3_accuracy"] = round(summary["top3_correct"] / count, 6)
    metrics = json.loads(Path(config["metrics_path"]).read_text())
    result = {
        "summary": summary,
        "queries_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "matching_config": config["matching"],
        "source_hashes": {
            name: entry["sha256"] for name, entry in metrics["source"]["files"].items()
        },
        "predictions": predictions,
    }
    Path(config["results_path"]).write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    )
    write_report(config, metrics, result)
    logger.info(
        "Top-1: %s/%s; top-3: %s/%s (unreviewed mini-set)",
        summary["top1_correct"],
        count,
        summary["top3_correct"],
        count,
    )
    return result


def write_report(config: dict, metrics: dict, result: dict) -> None:
    """Build a report from saved inventory and prediction records."""
    summary = result["summary"]
    top1, top3 = summary["top1_correct"], summary["top3_correct"]
    pct1, pct3 = summary["top1_accuracy"] * 100, summary["top3_accuracy"] * 100
    ambiguous = summary["underspecified_queries"]
    lines = [
        "# Medication reference and matching - TASK 4",
        "",
        "**France BDPM fallback, not Moroccan market coverage.**",
        "",
        "The Moroccan CNOPS open-data listing was found, but the portal/API returned",
        "HTTP 503 on 2026-10-26. No commercial listing was scraped. Official French",
        "bulk specialty/composition/presentation files are used instead.",
        "",
        f"Loaded specialties: **{metrics['records']}**.",
        f"Alias records: **{metrics['aliases']}**.",
        f"With source active-substance names: {metrics['with_dci']}.",
        f"With a product-name strength fragment: {metrics['with_name_strength']}.",
        f"With at least one source presentation: {metrics['with_presentation']}.",
        "",
        "No Arabic official brand names or Moroccan PPV values are supplied:",
        "brand_name_ar and price_ppv remain null. Arabic/Arabizi/typo aliases are",
        "programmatic and flagged synthetic; they are not approved product names.",
        "",
        "## Source provenance",
        "",
        "Producer: Base de données publique des médicaments (ANSM/HAS/UNCAM), France.",
        "Source and update dates must accompany reuse. This derived prototype is",
        "not an official service or endorsement; data may have changed since capture.",
        "[Download "
        "terms](https://base-donnees-publique.medicaments.gouv.fr/telechargement)",
        "[Licence Ouverte "
        "1.0](https://base-donnees-publique.medicaments.gouv.fr/docs/telechargement/licence_bdpm.pdf)",
        "",
        "| File | Published date observed on source page | SHA256 of original bytes |",
        "| --- | --- | --- |",
    ]
    for name, item in metrics["source"]["files"].items():
        lines.append(f"| {name} | {item['published_date']} | `{item['sha256']}` |")
    lines += [
        "",
        "## Evaluation on 50 authored review queries",
        "",
        "This is an unreviewed, small, purposive mini-set, not a gold or independent",
        "test distribution. Expected sets were labelled from the source catalogue.",
        "Underspecified queries accept any listed family/attribute-compatible ID;",
        "a correct hit does not mean unique product identification. The matcher",
        "retains ambiguity flags. These labels require the user's review.",
        "",
        "| Measure | Value |",
        "| --- | ---: |",
        f"| Top-1 acceptable-ID accuracy | {top1}/50 ({pct1:.2f}%) |",
        f"| Top-3 acceptable-ID accuracy | {top3}/50 ({pct3:.2f}%) |",
        f"| Queries with multiple acceptable IDs | {ambiguous} |",
        "",
        "Source labels: [50 queries](examples/medication_queries_50.json).",
        "Predictions and count provenance: [results](medication_query_results.json).",
        "",
        "## Failures",
        "",
    ]
    failures = [row for row in result["predictions"] if not row["top1_correct"]]
    lines += [
        f"- `{row['id']}`: {row['query']} (top-3 correct: {row['top3_correct']})."
        for row in failures
    ] or ["No top-1 errors on this limited, unreviewed mini-set."]
    lines += [
        "",
        "## Rebuild",
        "",
        "```bash",
        "make medications",
        "```",
        "",
        "Rebuild uses committed compressed source bytes and verifies hashes; "
        "no network",
        "is required. See [data instructions](../data/medications/README.md).",
        "",
        "## Semantics and limitations",
        "",
        "Brand_name is a derived lexical family; full_name preserves the source label.",
        "DCI holds source SA active-substance names, not a newly verified "
        "WHO-INN mapping.",
        "Laboratory holds the source marketing-authorization holder, not an inferred",
        "manufacturer. Presentation combines source labels; no package is "
        "selected for the user.",
        "DOSAGE is a verbatim product-strength fragment, never a recommended regimen.",
        "Source authorization and marketing statuses are preserved, "
        "including withdrawn",
        "or non-marketed records. They do not establish Moroccan "
        "authorization or stock.",
        "Similarity scores combine RapidFuzz and character TF-IDF. They are "
        "not probabilities.",
        "Explicit strengths/forms constrain candidates. Approximate "
        "spellings can still",
        "collide; close alternatives require clarification, not automatic "
        "substitution.",
        "Phonetic rules and generated Arabic spellings require native-speaker review.",
        "Synthetic aliases are not canonical Arabic names and are not evaluation gold.",
        "No diagnosis, dosage advice, therapeutic equivalence or "
        "substitution is inferred.",
    ]
    Path(config["report_path"]).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    """Evaluate the fixed mini-set with configured, deterministic matching."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/medications.yaml"))
    args = parser.parse_args()
    evaluate(load_config(args.config))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
