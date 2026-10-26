"""Fine-tune a local encoder with intent and token heads, using optional extras."""

import argparse
import json
import random
from pathlib import Path


def main() -> None:
    """Train on train only; local paths avoid unreviewed model/license downloads."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=40)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.steps < 1 or not args.model_path.is_dir():
        parser.error("Supply a local encoder snapshot and positive training steps")
    import torch
    from transformers import AutoModel, AutoTokenizer

    from pharma_assistant.data_tools.nlu_dataset import read_jsonl, validate_rows

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.use_deterministic_algorithms(True)
    rows = read_jsonl(Path("data/nlu/generated/train.jsonl"))
    validate_rows(rows)
    intents = sorted({r["intent"] for r in rows})
    tags = ["O"] + [
        prefix + kind
        for kind in sorted({e["type"] for r in rows for e in r["entities"]})
        for prefix in ["B-", "I-"]
    ]
    tokenizer = AutoTokenizer.from_pretrained(
        str(args.model_path), local_files_only=True, use_fast=True
    )
    encoder = AutoModel.from_pretrained(str(args.model_path), local_files_only=True)
    intent_head = torch.nn.Linear(encoder.config.hidden_size, len(intents))
    token_head = torch.nn.Linear(encoder.config.hidden_size, len(tags))
    parameters = (
        list(encoder.parameters())
        + list(intent_head.parameters())
        + list(token_head.parameters())
    )
    optimizer = torch.optim.AdamW(parameters, lr=2e-5)
    encoder.train()
    losses = []
    for step in range(args.steps):
        row = rows[step % len(rows)]
        batch = tokenizer(
            row["text"],
            return_tensors="pt",
            return_offsets_mapping=True,
            truncation=True,
            max_length=128,
        )
        offsets = batch.pop("offset_mapping")[0].tolist()
        labels = []
        for start, end in offsets:
            if start == end:
                labels.append(-100)
                continue
            entity = next(
                (e for e in row["entities"] if e["start"] <= start and end <= e["end"]),
                None,
            )
            tag = (
                "O"
                if entity is None
                else ("B-" if start == entity["start"] else "I-") + entity["type"]
            )
            labels.append(tags.index(tag))
        hidden = encoder(**batch).last_hidden_state
        loss = torch.nn.functional.cross_entropy(
            intent_head(hidden[:, 0]), torch.tensor([intents.index(row["intent"])])
        ) + torch.nn.functional.cross_entropy(
            token_head(hidden).view(-1, len(tags)),
            torch.tensor(labels),
            ignore_index=-100,
        )
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach()))
    args.output.mkdir(parents=True, exist_ok=True)
    encoder.save_pretrained(args.output)
    tokenizer.save_pretrained(args.output)
    torch.save(
        {
            "intent_head": intent_head.state_dict(),
            "token_head": token_head.state_dict(),
        },
        args.output / "heads.pt",
    )
    (args.output / "training.json").write_text(
        json.dumps(
            {
                "seed": args.seed,
                "steps": args.steps,
                "losses": losses,
                "intents": intents,
                "tags": tags,
            },
            indent=2,
        )
        + "\n"
    )
    print("Encoder training completed; evaluate on dev before any gold run.")


if __name__ == "__main__":
    main()
