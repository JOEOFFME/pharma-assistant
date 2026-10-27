"""Explicit single-request OpenRouter smoke check; requires the user's local key."""

import os

from pharma_assistant.nlp.openrouter import OpenRouterProvider


def main() -> None:
    """Make one paid-provider request without displaying credentials or HTTP bodies."""
    try:
        provider = OpenRouterProvider(
            os.getenv("OPENROUTER_API_KEY", ""), os.getenv("OPENROUTER_MODEL", "")
        )
    except ValueError:
        raise SystemExit("Set OPENROUTER_API_KEY and OPENROUTER_MODEL first.") from None
    try:
        result = provider.plan("3tini list dyal a9rab les pharmacy lya")
    except (ValueError, OSError):
        raise SystemExit(
            "OpenRouter check failed. Check your model's structured-output support, "
            "key, account credit, provider availability and network connection."
        ) from None
    print("OpenRouter connection and structured-output parsing: OK")
    print(f"Model: {provider.model}")
    print(f"Interpreted intent: {result.intent}")
    if result.intent != "pharmacy_info_location":
        raise SystemExit("Connection worked, but the sample intent needs review.")


if __name__ == "__main__":
    main()
