"""Train two small supervised models on train only; compare on dev only."""

import hashlib
import json
from pathlib import Path

from pharma_assistant.data_tools.nlu_dataset import read_jsonl, validate_rows
from pharma_assistant.eval.text_baseline import metrics
from pharma_assistant.nlp.supervised import SupervisedNLU


def main() -> None:
    """Save actual dev results and a model card without inspecting final gold."""
    train = read_jsonl(Path("data/nlu/generated/train.jsonl"))
    dev = read_jsonl(Path("data/nlu/generated/dev.jsonl"))
    validate_rows(train)
    validate_rows(dev)
    results = {}
    for analyzer in ["word", "char_wb"]:
        model = SupervisedNLU(analyzer=analyzer, seed=42)
        model.fit(train)
        predictions = [model.predict(row["text"]) for row in dev]
        result = metrics(dev, predictions)
        result["examples"] = [
            {
                "id": r["id"],
                "text": r["text"],
                "expected_intent": r["intent"],
                "prediction": p,
            }
            for r, p in zip(dev, predictions, strict=True)
        ]
        path = Path(f"models/{analyzer}/model.pkl")
        model.save(path)
        result["model_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        results[analyzer] = result
        (path.parent / "model_card.md").write_text(
            "# Small-data supervised prototype\n\n"
            "Trained on 520 assistant/synthetic rows; 50 development rows.\n"
            "Not a clinical model, encoder benchmark or final gold result.\n"
            "Load pickle files only from trusted local training.\n",
            encoding="utf-8",
        )
    Path("docs/supervised_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                k: {
                    m: r[m]
                    for m in [
                        "rows",
                        "intent_accuracy",
                        "intent_macro_f1",
                        "entity_exact_micro",
                    ]
                }
                for k, r in results.items()
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
