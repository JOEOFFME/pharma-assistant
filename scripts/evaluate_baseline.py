"""Run the Task-6 baseline on explicit human gold or the user-reviewed draft."""

import argparse
import json
from pathlib import Path

from pharma_assistant.eval.text_baseline import evaluate
from pharma_assistant.pipeline.text_pipeline import TextPipeline


def main() -> None:
    """Select cohort explicitly; never change annotation verification or authorship."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/baseline.yaml"))
    parser.add_argument("--reviewed-draft", action="store_true")
    parser.add_argument(
        "--output", type=Path, default=Path("docs/baseline_results.json")
    )
    args = parser.parse_args()
    reference = Path(
        "data/nlu/gold_review.jsonl"
        if args.reviewed_draft
        else "data/nlu/gold_human.jsonl"
    )
    if args.reviewed_draft:
        manifest = json.loads(Path("docs/draft_review_attestation.json").read_text())
        import hashlib

        source = Path("data/nlu/gold_human_draft.txt")
        if (
            manifest["draft_sha256"] != hashlib.sha256(source.read_bytes()).hexdigest()
            or manifest["annotations_sha256"]
            != hashlib.sha256(reference.read_bytes()).hexdigest()
        ):
            raise ValueError("Review attestation hashes do not match current files")
    pipeline = TextPipeline.from_config(args.config)
    result = evaluate(
        pipeline,
        reference,
        args.output,
        cohort="user_reviewed_draft" if args.reviewed_draft else "human_gold",
    )
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in {"examples", "intent_confusion"}
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
