"""Lock reviewed gold candidates; this command cannot supply missing human review."""

import argparse
import logging
from pathlib import Path

from pharma_assistant.data_tools.fetch_pharmacies import load_config
from pharma_assistant.data_tools.gold_review import lock_gold
from pharma_assistant.data_tools.nlu_dataset import build_dataset


def main() -> None:
    """Require per-record approval and matching hashes before gold admission."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/nlu.yaml"))
    args = parser.parse_args()
    config = load_config(args.config)
    build_dataset(config)
    lock_gold(
        Path(config["gold_candidates_path"]),
        Path(config["gold_review_path"]),
        Path(config["gold_test_path"]),
        Path(config["gold_lock_path"]),
    )
    logging.getLogger(__name__).info("Gold locked after declared human review")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
