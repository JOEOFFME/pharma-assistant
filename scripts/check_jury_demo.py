"""Check jury requests against the real API and local source databases."""

import argparse
import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from pharma_assistant.api.app import create_app


def main() -> None:
    """Fail clearly if a demonstrated route or expected answer regresses."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-voice", action="store_true")
    args = parser.parse_args()
    questions = json.loads(
        Path("web/assets/demo-questions.json").read_text(encoding="utf-8")
    )
    failed = 0
    with TestClient(create_app()) as client:
        for question in questions:
            response = client.post(
                "/v1/assistant/text",
                json={k: question[k] for k in ("text", "language_hint")},
            )
            result = response.json()
            ok = (
                response.status_code == 200
                and result["analysis"]["intent"]["label"] == question["intent"]
                and all(s in result["answer"] for s in question["answer_contains"])
            )
            if question["id"] == "city":
                ok = ok and bool(result.get("pharmacies"))
            print(f"{'PASS' if ok else 'FAIL'} {question['id']}")
            failed += not ok
        scenarios = json.loads(
            Path("web/assets/jury-scenarios.json").read_text(encoding="utf-8")
        )
        for question in scenarios:
            response = client.post(
                "/v1/demo/assistant/text",
                json={k: question[k] for k in ("text", "language_hint")},
            )
            result = response.json()
            ok = (
                response.status_code == 200
                and result.get("synthetic") is True
                and result["scenario_kind"] == question["kind"]
                and all(s in result["answer"] for s in question["answer_contains"])
            )
            print(f"{'PASS' if ok else 'FAIL'} fictional scenario: {question['id']}")
            failed += not ok
        response = client.get(
            "/v1/pharmacies/map",
            params={"lat": 34.0209, "lon": -6.8416, "radius_km": 5},
        )
        map_ok = response.status_code == 200 and response.json()["count"] > 0
        print(f"{'PASS' if map_ok else 'FAIL'} Rabat map")
        failed += not map_ok
        voice = client.get("/v1/voice/status").json()
        print(f"Voice prerequisites: {'READY' if voice.get('ready') else 'NOT READY'}")
        if not voice.get("ready"):
            print("See docs/jury_demo.md for voice setup before the presentation.")
            failed += args.require_voice
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
