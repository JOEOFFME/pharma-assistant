"""Evaluate a locally fine-tuned encoder on explicit dev or verified human data."""

import argparse
import hashlib
import json
from pathlib import Path


def main() -> None:
    """Use local models and explicit reference data, without silent gold admission."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument(
        "--reference", type=Path, default=Path("data/nlu/generated/dev.jsonl")
    )
    parser.add_argument("--human-gold", action="store_true")
    parser.add_argument(
        "--output", type=Path, default=Path("reports/encoder_results.json")
    )
    args = parser.parse_args()
    import torch
    from transformers import AutoModel, AutoTokenizer

    from pharma_assistant.data_tools.nlu_dataset import read_jsonl, validate_rows
    from pharma_assistant.eval.text_baseline import metrics

    rows = read_jsonl(args.reference)
    validate_rows(rows)
    if not rows:
        parser.error("Reference is empty")
    if args.human_gold and any(
        r["source"] != "human" or not r["verified"] for r in rows
    ):
        parser.error("Human gold requires verified human-source rows")
    metadata = json.loads((args.model_dir / "training.json").read_text())
    intents, tags = metadata["intents"], metadata["tags"]
    tokenizer = AutoTokenizer.from_pretrained(
        str(args.model_dir), local_files_only=True, use_fast=True
    )
    encoder = AutoModel.from_pretrained(str(args.model_dir), local_files_only=True)
    intent_head = torch.nn.Linear(encoder.config.hidden_size, len(intents))
    token_head = torch.nn.Linear(encoder.config.hidden_size, len(tags))
    heads = torch.load(
        args.model_dir / "heads.pt", map_location="cpu", weights_only=True
    )
    intent_head.load_state_dict(heads["intent_head"])
    token_head.load_state_dict(heads["token_head"])
    encoder.eval()
    intent_head.eval()
    token_head.eval()
    predictions = []
    with torch.inference_mode():
        for row in rows:
            text = row["text"]
            batch = tokenizer(
                text,
                return_tensors="pt",
                return_offsets_mapping=True,
                truncation=True,
                max_length=128,
            )
            offsets = batch.pop("offset_mapping")[0].tolist()
            hidden = encoder(**batch).last_hidden_state
            label = intents[int(intent_head(hidden[:, 0]).argmax(-1))]
            predicted_tags = token_head(hidden)[0].argmax(-1).tolist()
            entities = []
            for (start, end), tag_id in zip(offsets, predicted_tags, strict=True):
                tag = tags[tag_id]
                if start == end or tag == "O":
                    continue
                kind = tag[2:]
                if (
                    tag.startswith("I-")
                    and entities
                    and entities[-1]["type"] == kind
                    and (
                        not text[entities[-1]["end"] : start]
                        or text[entities[-1]["end"] : start].isspace()
                    )
                ):
                    entities[-1]["end"] = end
                    entities[-1]["text"] = text[entities[-1]["start"] : end]
                else:
                    entities.append(
                        {
                            "type": kind,
                            "text": text[start:end],
                            "start": start,
                            "end": end,
                        }
                    )
            predictions.append(
                {
                    "input": {"raw_text": text},
                    "intent": {"label": label},
                    "entities": entities,
                }
            )
    result = metrics(rows, predictions)
    result["reference"] = {
        "path": str(args.reference),
        "sha256": hashlib.sha256(args.reference.read_bytes()).hexdigest(),
        "cohort": "human_gold" if args.human_gold else "development",
    }
    result["examples"] = [
        {"id": r["id"], "prediction": p} for r, p in zip(rows, predictions, strict=True)
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: result[k]
                for k in [
                    "rows",
                    "intent_accuracy",
                    "intent_macro_f1",
                    "entity_exact_micro",
                ]
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
