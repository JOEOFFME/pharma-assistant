"""Evaluate only user-recorded audio listed with human reference transcripts."""

import argparse
import json
from collections import defaultdict
from pathlib import Path

from pharma_assistant.asr.transcriber import WhisperTranscriber
from pharma_assistant.data_tools.fetch_pharmacies import load_config
from pharma_assistant.eval.speech import speech_metrics


def main() -> None:
    """Require real audio/transcripts; output per-variety WER/CER and hypotheses."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--config", type=Path, default=Path("configs/asr.yaml"))
    parser.add_argument(
        "--output", type=Path, default=Path("reports/speech_results.json")
    )
    args = parser.parse_args()
    records = [
        json.loads(line)
        for line in args.manifest.read_text().splitlines()
        if line.strip()
    ]
    if not records:
        parser.error("No recorded audio manifest entries")
    transcriber = WhisperTranscriber(load_config(args.config))
    pairs = defaultdict(list)
    outputs = []
    for row in records:
        transcript = transcriber.transcribe(args.manifest.parent / row["audio_path"])
        pairs[row["language"]].append((row["reference_text"], transcript.text))
        outputs.append({**row, "hypothesis": transcript.text})
    report = {
        "by_language": {k: speech_metrics(v) for k, v in pairs.items()},
        "recordings": outputs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report["by_language"], indent=2))


if __name__ == "__main__":
    main()
