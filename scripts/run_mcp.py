"""Expose Pharma-AI read-only tools to local MCP clients over UTF-8 stdio."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from pharma_assistant.nlp.agent import PharmacyTools
from pharma_assistant.nlp.mcp_stdio import serve
from pharma_assistant.nlp.openrouter import OpenRouterProvider
from pharma_assistant.pipeline.text_pipeline import TextPipeline


def main() -> None:
    """Keep local data/config paths independent of the MCP client's directory."""
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    load_dotenv(root / ".env", override=False)
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    provider = (
        OpenRouterProvider(
            key,
            os.getenv("OPENROUTER_MODEL", "").strip() or "openai/gpt-4.1",
            os.getenv("OPENROUTER_FALLBACK_MODEL", "anthropic/claude-sonnet-4.6"),
        )
        if key
        else None
    )
    serve(PharmacyTools(TextPipeline.from_config(), provider), sys.stdin, sys.stdout)


if __name__ == "__main__":
    main()
