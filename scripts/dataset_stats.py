"""Build/check NLU data and report class balance, language mix and lengths."""

import argparse
import json
import logging
from pathlib import Path

from pharma_assistant.data_tools.fetch_pharmacies import load_config
from pharma_assistant.data_tools.nlu_dataset import build_dataset

logger = logging.getLogger(__name__)


def main() -> None:
    """Regenerate deterministic splits and the statistics report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/nlu.yaml"))
    args = parser.parse_args()
    stats = build_dataset(load_config(args.config))
    logger.info("%s", json.dumps(stats, ensure_ascii=False))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
