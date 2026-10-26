"""Admit gold data only after explicit, record-bound human review."""

import hashlib
import json
from datetime import datetime
from pathlib import Path

from pharma_assistant.data_tools.nlu_dataset import (
    digest,
    read_jsonl,
    validate_rows,
    write_jsonl,
)


def lock_gold(
    candidates: Path, review_path: Path, output: Path, lock_path: Path
) -> None:
    """Seal reviewed annotations; absent reviews fail without creating gold files."""
    if output.exists() or lock_path.exists():
        raise ValueError(
            "Existing gold files are immutable; use a new versioned destination"
        )
    rows = read_jsonl(candidates)
    validate_rows(rows)
    if len(rows) < 100:
        raise ValueError("Gold requires at least 100 reviewed examples")
    reviews = json.loads(review_path.read_text(encoding="utf-8"))["rows"]
    by_id = {item["id"]: item for item in reviews}
    if len(by_id) != len(reviews) or set(by_id) != {row["id"] for row in rows}:
        raise ValueError("Review IDs must exactly match the candidate set")
    admitted = []
    for row in rows:
        review = by_id[row["id"]]
        if (
            review.get("approved") is not True
            or not str(review.get("reviewed_by") or "").strip()
        ):
            raise ValueError(f"Human review missing for {row['id']}")
        if review.get("example_sha256") != digest(row):
            raise ValueError(f"Review hash mismatch for {row['id']}")
        try:
            reviewed_at = datetime.fromisoformat(review["reviewed_at"])
        except (ValueError, TypeError, KeyError) as exc:
            raise ValueError("An explicit ISO review timestamp is required") from exc
        if reviewed_at.utcoffset() is None:
            raise ValueError("Review timestamps need a timezone")
        admitted.append(
            {
                **row,
                "review_status": "human_verified",
                "reviewed_by": review["reviewed_by"],
                "reviewed_at": review["reviewed_at"],
            }
        )
    write_jsonl(output, admitted)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(
        json.dumps(
            {
                "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "review_file_sha256": hashlib.sha256(
                    review_path.read_bytes()
                ).hexdigest(),
                "rows": len(admitted),
                "status": "human_review_declared",
                "note": "Audit metadata, not cryptographic proof of reviewer identity",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def load_locked_gold(path: Path, lock_path: Path) -> list[dict]:
    """Reject missing, changed or unreviewed gold instead of silently evaluating it."""
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if hashlib.sha256(path.read_bytes()).hexdigest() != lock["sha256"]:
        raise ValueError("Gold hash mismatch")
    rows = read_jsonl(path)
    validate_rows(rows)
    if len(rows) < 100 or len(rows) != lock["rows"]:
        raise ValueError("Invalid gold size")
    if lock.get("status") != "human_review_declared":
        raise ValueError("Invalid gold review status")
    for row in rows:
        if row.get("review_status") != "human_verified":
            raise ValueError("Unreviewed records in gold")
        if not str(row.get("reviewed_by") or "").strip():
            raise ValueError("Missing gold reviewer")
        try:
            reviewed_at = datetime.fromisoformat(row["reviewed_at"])
        except (ValueError, TypeError, KeyError) as exc:
            raise ValueError("Missing gold review timestamp") from exc
        if reviewed_at.utcoffset() is None:
            raise ValueError("Gold review timestamp needs a timezone")
    return rows
