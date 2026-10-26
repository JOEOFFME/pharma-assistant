"""Compare baseline, supervised and hybrid on dev; LLM needs real credentials."""

import json
import pickle
from pathlib import Path

from pharma_assistant.data_tools.nlu_dataset import read_jsonl
from pharma_assistant.eval.text_baseline import metrics
from pharma_assistant.pipeline.hybrid import HybridPipeline
from pharma_assistant.pipeline.text_pipeline import TextPipeline


def main() -> None:
    """Load only models produced locally by make train-nlu; never uploaded pickle."""
    rows = read_jsonl(Path("data/nlu/generated/dev.jsonl"))
    baseline = TextPipeline.from_config()
    learned = pickle.loads(Path("models/char_wb/model.pkl").read_bytes())
    pipelines = {"baseline": baseline, "hybrid": HybridPipeline(baseline, learned)}
    result = {}
    for name, pipeline in pipelines.items():
        predictions = [
            pipeline.analyze(r["text"]).model_dump(mode="json", by_alias=True)
            for r in rows
        ]
        result[name] = metrics(rows, predictions)
    result["llm"] = {
        "status": "not_run",
        "reason": "No real provider credentials configured; FakeLLM is tests only",
    }
    result["encoder"] = {
        "status": "not_run",
        "reason": "No local encoder snapshots supplied; "
        "optional fine-tuning command provided",
    }
    Path("docs/track_comparison.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                k: {
                    m: v.get(m)
                    for m in ["intent_accuracy", "intent_macro_f1", "status"]
                }
                for k, v in result.items()
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
