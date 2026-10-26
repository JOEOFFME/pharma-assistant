"""Export the response JSON Schema from its single Pydantic source of truth."""

import argparse
import json
import logging
from pathlib import Path

from pharma_assistant.api.schemas import AnalysisResponse, NLUAnnotation

logger = logging.getLogger(__name__)


def main() -> None:
    """Write a deterministic schema to a caller-selected, portable path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("docs/response_v1.schema.json")
    )
    parser.add_argument(
        "--annotation-output",
        type=Path,
        default=Path("docs/nlu_annotation.schema.json"),
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(AnalysisResponse.model_json_schema(), ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    args.annotation_output.parent.mkdir(parents=True, exist_ok=True)
    args.annotation_output.write_text(
        json.dumps(NLUAnnotation.model_json_schema(), ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    logger.info("Exported response and annotation schemas")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
