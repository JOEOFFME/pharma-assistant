"""Exact span-level and intent metrics with explicit annotation provenance."""

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import get_args

from pharma_assistant.api.schemas import IntentLabel
from pharma_assistant.data_tools.nlu_dataset import read_jsonl, validate_rows


def metrics(rows: list[dict], predictions: list[dict]) -> dict:
    """Compute all-eight-class macro F1 and micro exact type/start/end entity F1."""
    if not rows or len(rows) != len(predictions):
        raise ValueError("Need nonempty aligned reference/prediction rows")
    labels = list(get_args(IntentLabel))
    confusion = {label: dict.fromkeys(labels, 0) for label in labels}
    tp = fp = fn = 0
    per_type: dict[str, Counter] = {}
    for row, prediction in zip(rows, predictions, strict=True):
        if prediction["input"]["raw_text"] != row["text"]:
            raise ValueError("Prediction/reference texts are not aligned")
        predicted = prediction["intent"]["label"]
        confusion[row["intent"]][predicted] += 1
        expected = Counter((e["type"], e["start"], e["end"]) for e in row["entities"])
        actual = Counter(
            (e["type"], e["start"], e["end"]) for e in prediction["entities"]
        )
        correct, extra, missing = (
            expected & actual,
            actual - expected,
            expected - actual,
        )
        tp += sum(correct.values())
        fp += sum(extra.values())
        fn += sum(missing.values())
        for counts, key in [(correct, "tp"), (extra, "fp"), (missing, "fn")]:
            for (kind, _, _), count in counts.items():
                per_type.setdefault(kind, Counter())[key] += count

    def entity_result(a: int, b: int, c: int) -> dict:
        return {
            "tp": a,
            "fp": b,
            "fn": c,
            "precision": a / (a + b) if a + b else 0.0,
            "recall": a / (a + c) if a + c else 0.0,
            "f1": 2 * a / (2 * a + b + c) if 2 * a + b + c else 0.0,
        }

    f1 = []
    for label in labels:
        correct = confusion[label][label]
        extra = sum(confusion[other][label] for other in labels if other != label)
        missing = sum(confusion[label][other] for other in labels if other != label)
        f1.append(entity_result(correct, extra, missing)["f1"])
    return {
        "rows": len(rows),
        "intent_accuracy": sum(confusion[k][k] for k in labels) / len(rows),
        "intent_macro_f1": sum(f1) / len(f1),
        "intent_confusion": confusion,
        "entity_exact_micro": entity_result(tp, fp, fn),
        "entity_by_type": {
            k: entity_result(v["tp"], v["fp"], v["fn"])
            for k, v in sorted(per_type.items())
        },
    }


def evaluate(pipeline, reference: Path, output: Path, *, cohort: str) -> dict:
    """Keep saved predictions traceable; never silently fall back to a draft as gold."""
    rows = read_jsonl(reference)
    validate_rows(rows)
    if cohort == "human_gold" and any(
        r["source"] != "human" or not r["verified"] for r in rows
    ):
        raise ValueError("Human gold requires verified human annotations")
    if not rows:
        raise ValueError("Evaluation reference is empty; no metrics can be claimed")
    predictions = []
    for row in rows:
        prediction = pipeline.analyze(row["text"]).model_dump(
            mode="json", by_alias=True
        )
        # Exclude request UUID and wall-clock latency from deterministic artifacts.
        prediction.pop("request_id")
        prediction.pop("latency_ms")
        predictions.append(prediction)
    result = metrics(rows, predictions)
    result["reference"] = {
        "path": reference.as_posix(),
        "sha256": hashlib.sha256(reference.read_bytes()).hexdigest(),
        "cohort": cohort,
        "intent_reference": (
            "user-reviewed draft labels" if cohort != "human_gold" else "human gold"
        ),
        "entity_reference": (
            "automatic proposals; provisional agreement, not verified gold F1"
            if cohort != "human_gold"
            else "human gold"
        ),
        "limitations": (
            [
                "Exploratory baseline: developer has seen draft examples",
                "Two draft greetings overlap development data",
                "No tuning or training on this evaluation run",
            ]
            if cohort != "human_gold"
            else []
        ),
    }
    result["examples"] = [
        {
            "id": row["id"],
            "text": row["text"],
            "expected_intent": row["intent"],
            "prediction": pred,
        }
        for row, pred in zip(rows, predictions, strict=True)
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return result
