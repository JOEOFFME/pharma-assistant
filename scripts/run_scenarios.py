"""Run 30 reproducible text scenarios, retaining every pass and failure."""

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pharma_assistant.pipeline.text_pipeline import TextPipeline


def main() -> None:
    """Check real pipeline contracts; these are scenarios, not independent gold."""
    rows = json.loads(Path("docs/examples/nlu_annotation_examples.json").read_text())
    chosen = []
    for language in ["darija_ar", "darija_latn", "ar", "fr", "mixed"]:
        chosen.extend(
            next(r for r in rows if r["language"] == language and r["intent"] == intent)
            for intent in [
                "check_availability",
                "request_medication",
                "pharmacy_info_phone",
                "pharmacy_info_location",
                "pharmacy_info_hours",
                "out_of_scope",
                "price_inquiry",
                "greeting_smalltalk",
            ]
        )
    pipeline = TextPipeline.from_config()
    results = []
    for row in chosen:
        prediction = pipeline.analyze(row["text"], language_hint=row["language"])
        results.append(
            {
                "id": row["id"],
                "text": row["text"],
                "expected_intent": row["intent"],
                "passed": prediction.intent.label == row["intent"],
                "prediction": prediction.model_dump(mode="json", by_alias=True),
            }
        )
    report = {
        "scenario_count": len(results),
        "passed": sum(r["passed"] for r in results),
        "failed": sum(not r["passed"] for r in results),
        "status": "development scenarios; not final gold",
        "results": results,
    }
    date = datetime.now(ZoneInfo("Africa/Casablanca")).strftime("%Y%m%d")
    destination = Path("reports") / f"eval_{date}.json"
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    Path("docs/scenario_results.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    lines = [
        "# End-to-end text scenarios",
        "",
        f"Observed: {report['passed']}/{len(results)} matching primary intents. "
        "Failures retained.",
        "",
        "| Scenario | Message | Expected | Actual | Pass |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines.extend(
        f"| {r['id']} | {r['text']} | {r['expected_intent']} | "
        f"{r['prediction']['intent']['label']} | {r['passed']} |"
        for r in results
    )
    Path("docs/10_test_scenarios.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "results"}))


if __name__ == "__main__":
    main()
