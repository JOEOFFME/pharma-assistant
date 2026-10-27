"""One explicit request to check the configured data-grounded main model."""

import os
from pathlib import Path
from urllib.error import HTTPError

from dotenv import load_dotenv

from pharma_assistant.api.data_chat import validate_reply
from pharma_assistant.nlp.openrouter import OpenRouterProvider, compose_reply


def main() -> None:
    """Use a public sample question; never display credentials or error bodies."""
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    try:
        provider = OpenRouterProvider(
            os.getenv("OPENROUTER_API_KEY", ""),
            (os.getenv("OPENROUTER_MODEL", "").strip() or "openai/gpt-4.1"),
            os.getenv("OPENROUTER_FALLBACK_MODEL", "anthropic/claude-sonnet-4.6"),
        )
    except ValueError:
        raise SystemExit("Add OPENROUTER_API_KEY to .env first.") from None
    text = "Bonjour, où je peux trouver Panadol ?"
    context = {
        "pharmacies": [],
        "live_stock": "unverified",
        "current_duty": "unverified",
    }
    try:
        reply, model = compose_reply(provider, text, context, [], "fr")
        validate_reply(reply, context, text)
    except HTTPError as error:
        explanations = {
            401: "Key rejected: check OPENROUTER_API_KEY.",
            402: "OpenRouter credits are required for this request.",
            403: "This key or account is not permitted to use this model.",
            404: "No compatible model/provider endpoint was found.",
            429: "OpenRouter rate limit reached; retry later.",
        }
        raise SystemExit(
            explanations.get(
                error.code,
                f"OpenRouter HTTP {error.code}: retry or check the model/provider.",
            )
        ) from None
    except (ValueError, OSError):
        raise SystemExit(
            "OpenRouter check failed. Check the key, account credit, model's JSON "
            "support, provider availability and network. No secret is displayed."
        ) from None
    print("OpenRouter main-model connection and grounded reply: OK")
    print(f"Model used: {model}")
    print(reply.answer)


if __name__ == "__main__":
    main()
