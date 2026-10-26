"""Measure explicit normalization and resolution ablations on the reviewed draft."""

import json
from pathlib import Path
from time import perf_counter

from pharma_assistant.data_tools.nlu_dataset import read_jsonl
from pharma_assistant.eval.text_baseline import metrics
from pharma_assistant.pipeline.text_pipeline import TextPipeline


def main() -> None:
    """Keep entity agreement provisional, and record actual wall-clock samples."""
    rows = read_jsonl(Path("data/nlu/gold_review.jsonl"))
    pipeline = TextPipeline.from_config()
    results = {}
    for name, normalize, resolve in [
        ("full", True, True),
        ("normalization_off", False, True),
        ("resolution_off", True, False),
    ]:
        pipeline.config.update(
            normalize_entities=normalize, resolve_medications=resolve
        )
        predictions = []
        latency = []
        for row in rows:
            start = perf_counter()
            prediction = pipeline.analyze(row["text"])
            latency.append((perf_counter() - start) * 1000)
            predictions.append(prediction.model_dump(mode="json", by_alias=True))
        result = metrics(rows, predictions)
        values = sorted(latency)
        result["latency_ms"] = {
            "p50": values[(len(values) - 1) // 2],
            "p95": values[int(0.95 * (len(values) - 1))],
            "samples": latency,
        }
        result["resolved_mentions"] = sum(
            bool(e.get("matched_id"))
            for p in predictions
            for e in p["entities"]
            if e["type"] == "MEDICATION"
        )
        result["reference_status"] = (
            "User-reviewed draft labels; entity agreement with automatic proposals"
        )
        result["examples"] = [
            {"id": r["id"], "prediction": p}
            for r, p in zip(rows, predictions, strict=True)
        ]
        results[name] = result
    Path("docs/ablation_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                k: {
                    m: v[m]
                    for m in [
                        "intent_accuracy",
                        "entity_exact_micro",
                        "latency_ms",
                        "resolved_mentions",
                    ]
                }
                for k, v in results.items()
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
