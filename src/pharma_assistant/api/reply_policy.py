"""Small presentation rules for direct requests and honest search attribution."""

import re

from pharma_assistant.nlp.health_reference import reference_answer, reference_for


def short_reply(baseline, analysis, text, history=None, location=None):
    """Answer a narrow source-backed example or ask only for the missing city."""
    reference = reference_for(text, history)
    explicit_web = re.search(r"\bweb\b|internet|recherche|cherche sur", text, re.I)
    asks_example = re.search(r"\bexemple\b|\bnom\b|smiya|smya|smit|اسم", text, re.I)
    personal = re.search(
        r"posologie|dosage|\bdose\b|combien|prendre|pour moi|pour mon"
        r"|enceinte|enfant|ناخد|جرعة",
        text,
        re.I,
    )
    names_medicine = re.search(r"\bm[eé]dicaments?\b|\bdwa\b|دواء|دوا", text, re.I)
    name_followup = re.search(r"dyalo|son nom|juste le nom|ghir sm", text, re.I)
    negated_example = re.search(r"\b(?:pas|sans|non|not)\b|ne .*utilis", text, re.I)
    if (
        reference
        and asks_example
        and (names_medicine or name_followup)
        and not personal
        and not explicit_web
        and not negated_example
    ):
        return reference_answer(reference, analysis.input.language, concise=True)
    medication = next(
        (
            e.text
            for e in analysis.entities
            if e.type == "MEDICATION" and e.assertion == "affirmed"
        ),
        None,
    )
    search = re.search(
        r"\bo[uù]\s+(?:puis[- ]je|je peux)\s+(?:chercher|trouver)\s+"
        r"(?:(?:du|le|de la|des)\s+)?([^?\n]{1,100})",
        text,
        re.I,
    )
    if search and not medication and "pharmac" not in search[1].casefold():
        medication = search[1].strip(" .!")
    availability = analysis.intent.label == "check_availability" or search
    if not medication or not availability or personal or explicit_web:
        return None
    if location is not None:
        return None
    for candidate in [analysis] + [
        baseline.analyze(t["text"])
        for t in reversed(history or [])
        if t["role"] == "user"
    ]:
        if any(
            e.type in {"LOCATION", "PHARMACY_NAME"} and e.assertion == "affirmed"
            for e in candidate.entities
        ):
            return None
    language = analysis.input.language
    answer = f"Dans quelle ville ou quel quartier cherchez-vous « {medication} » ?"
    if language == "darija_latn":
        answer = f"F achmen mdina wla 7ay kat9elleb 3la « {medication} » ?"
    elif language in {"ar", "darija_ar"}:
        answer = f"في أي مدينة أو حي تبحث عن « {medication} »؟"
    return {
        "answer": answer,
        "answer_source": "location_clarification",
        "model": None,
        "sources": [],
        "pharmacies": [],
        "actions": [{"type": "share_location", "label": "Partager ma position"}],
    }


def validate_search_attribution(answer: str, web_succeeded: bool) -> None:
    """Reject claimed online research when no successful web result exists."""
    if web_succeeded:
        return
    if re.search(
        r"repertoire|répertoire|catalogue|annuaire|sources enregistrées", answer, re.I
    ):
        return
    if re.search(
        r"\b(?:cette|ma|mes|notre)\s+recherches?\b"
        r"|(?:j.ai|nous avons)\s+(?:recherch[eé]|consult[eé])\b"
        r"|apr[eè]s (?:une |la )?recherche",
        answer,
        re.I,
    ):
        raise ValueError("Claimed research without successful search evidence")
