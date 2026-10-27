"""Deterministic supported-request routing with a separate medical-advice flag."""

import re

from pharma_assistant.api.schemas import IntentLabel
from pharma_assistant.nlp.normalize import normalize

PRIORITY = [
    "request_medication",
    "check_availability",
    "price_inquiry",
    "pharmacy_info_location",
    "pharmacy_info_hours",
    "pharmacy_info_phone",
    "greeting_smalltalk",
]


def phrase_in(text: str, phrase: str) -> bool:
    """Match normalized token boundaries, preserving original text elsewhere."""
    return (
        re.search(
            r"(?<!\w)" + re.escape(normalize(phrase, arabizi=False).text) + r"(?!\w)",
            text,
        )
        is not None
    )


def contains_medical_advice(text: str, config: dict) -> bool:
    """Use the shared clinical lexicon without treating unknown text as advice."""
    normalized = normalize(text, arabizi=False).text
    return any(phrase_in(normalized, phrase) for phrase in config["medical_advice"])


def classify_intent(text: str, config: dict) -> tuple[IntentLabel, bool, bool]:
    """Return primary intent, mixed unsupported clause flag and action ambiguity."""
    normalized = (
        normalize(text, arabizi=False).text
        if config.get("normalize_entities", True)
        else text.casefold()
    )
    advice = contains_medical_advice(text, config)
    found = [
        label
        for label in PRIORITY
        if any(phrase_in(normalized, p) for p in config["rules"][label])
    ]
    pharmacy_context = any(
        phrase_in(normalized, term) for term in config.get("pharmacy_terms", [])
    )
    nearby = any(phrase_in(normalized, term) for term in config.get("nearby_terms", []))
    if pharmacy_context and nearby and "pharmacy_info_location" not in found:
        found.append("pharmacy_info_location")
        found.sort(key=PRIORITY.index)
    # Clinical phrases alone cannot become stock requests due to quoted verbs.
    if advice and not any(
        label in found
        for label in [
            "check_availability",
            "price_inquiry",
            "pharmacy_info_location",
            "pharmacy_info_hours",
            "pharmacy_info_phone",
        ]
    ):
        return "out_of_scope", False, False
    substantive = [label for label in found if label != "greeting_smalltalk"]
    # A price or stock question containing 'voudrais/bghit' is a query about it.
    if "price_inquiry" in substantive or "check_availability" in substantive:
        substantive = [label for label in substantive if label != "request_medication"]
    if any(
        label in substantive
        for label in ["request_medication", "check_availability", "price_inquiry"]
    ):
        substantive = [
            label for label in substantive if not label.startswith("pharmacy_info_")
        ]
    if substantive:
        return substantive[0], advice, len(substantive) > 1
    return (
        ("out_of_scope" if advice or not found else "greeting_smalltalk"),
        False,
        False,
    )
