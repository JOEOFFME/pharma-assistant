"""Explicit live rehearsal of the research agent using a non-personal sample."""

import os
import sys
from pathlib import Path
from urllib.error import HTTPError

from dotenv import load_dotenv

from pharma_assistant.nlp.agent import run_agent
from pharma_assistant.nlp.openrouter import OpenRouterProvider
from pharma_assistant.pipeline.text_pipeline import TextPipeline


def main() -> None:
    """Use the private local key; never print secrets or raw provider errors."""
    sys.stdout.reconfigure(encoding="utf-8")
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    load_dotenv(root / ".env", override=False)
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise SystemExit("Add OPENROUTER_API_KEY to .env first.")
    provider = OpenRouterProvider(
        key,
        os.getenv("OPENROUTER_MODEL", "").strip() or "openai/gpt-4.1",
        os.getenv("OPENROUTER_FALLBACK_MODEL", "anthropic/claude-sonnet-4.6"),
    )
    try:
        result = run_agent(
            provider,
            TextPipeline.from_config(),
            "Vérifie sur le web : chnu smiya dyal dwa dyal la migraine ?",
            "darija_latn",
        )
    except FileNotFoundError:
        raise SystemExit(
            "Build the local databases by running scripts/start_service.py first."
        ) from None
    except HTTPError as error:
        raise SystemExit(
            f"OpenRouter HTTP {error.code}. "
            "Check key, credits, model and tool permissions."
        ) from None
    except (ValueError, OSError):
        raise SystemExit(
            "Agent check failed. Check network, model tool/JSON support "
            "and search permissions."
        ) from None
    if "search_health_web" not in result["tools_used"] or not any(
        s["kind"] == "web" for s in result["sources"]
    ):
        print(
            "Safe tool diagnostics:",
            ", ".join(result.get("tool_failures", [])) or "no successful web call",
        )
        raise SystemExit(
            "The model did not finish a cited web answer. Research is not validated; "
            "retry or check model/search settings."
        )
    print("Agent tool execution and cited web answer: OK")
    print("Model used:", result["model"])
    print(result["answer"])
    for source in result["sources"]:
        print(source["title"], source["url"])


if __name__ == "__main__":
    main()
