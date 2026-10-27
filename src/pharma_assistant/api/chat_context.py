"""Resolve directory follow-ups from user evidence and render honest local results."""

import re

from pharma_assistant.api.answers import MESSAGES, PRESENTATION_HELP, present_answer
from pharma_assistant.api.schemas import AnalysisResponse


def directory_context(baseline, text, history=None, location=None) -> dict | None:
    """Use explicit user places only; assistant offers supply intent, never facts."""
    from pharma_assistant.nlp.pharmacy_web import lookup_request

    if lookup_request(baseline, text, history):
        return None
    current = baseline.analyze(text)
    turns = [t["text"] for t in (history or []) if t["role"] == "user"]
    candidates = [current] + [baseline.analyze(t) for t in reversed(turns)]
    selected = next(
        (
            a
            for a in candidates
            if any(
                e.type in {"LOCATION", "PHARMACY_NAME"} and e.assertion == "affirmed"
                for e in a.entities
            )
        ),
        None,
    )
    if (
        selected is None
        and location is None
        and not (
            any(e.type == "MEDICATION" for e in current.entities)
            and re.search(
                r"où|ou |chercher|trouver|fin|nl9a|wach kayn|stock|disponib", text, re.I
            )
        )
    ):
        return None
    query = selected or current
    # Resolve city independently: a new pharmacy name must not erase the user's city.
    city_entity = next(
        (
            e
            for a in candidates
            for e in a.entities
            if e.type == "LOCATION" and e.assertion == "affirmed"
        ),
        None,
    )
    is_current_place = selected is current
    text_lower = text.casefold().strip(" .!?")
    confirmed = text_lower in {
        "oui",
        "oui merci",
        "oui svp",
        "yes",
        "ok",
        "daccord",
        "d'accord",
        "wakha",
        "iyeh",
        "اه",
        "نعم",
    }
    medicine_search = bool(
        any(e.type == "MEDICATION" for e in current.entities)
        and re.search(
            r"où|ou |chercher|trouver|fin|nl9a|wach kayn|stock|disponib", text_lower
        )
        and not re.search(r"prix|tarif|ch7al|bch7al|cnops|rembours", text_lower)
    )
    medical = (
        current.intent.label in {"check_availability", "request_medication"}
        and not current.contains_out_of_scope_request
        and any(e.type == "MEDICATION" for e in current.entities)
    )
    directory_words = bool(
        re.search(
            r"pharmac|صيدلي|pres de moi|près de moi|a9rab|9rib|coordonn", text_lower
        )
    )
    location_reply = is_current_place and (
        len(text.split()) <= 10
        and not re.search(
            r"migraine|traitement|posologie|dose|combien.*prendre|[?؟]"
            r"|\b(?:quel|quelle|comment|pourquoi|quand|what|how|weather)\b",
            text_lower,
        )
    )
    # A positive response needs a preceding directory offer or pharmacy request.
    offered = any(
        t["role"] == "assistant"
        and re.search(r"pharmac|صيدلي|coordonn", t["text"], re.I)
        for t in (history or [])[-2:]
    )
    requested = any(
        re.search(r"pharmac|صيدلي|pres de moi|près de moi|a9rab", t, re.I)
        for t in turns[-3:]
    )
    wanted = (
        location_reply
        or directory_words
        or medicine_search
        or medical
        or (confirmed and (offered or requested))
    )
    if medicine_search or medical:
        query = current
    if city_entity and not any(e.type == "LOCATION" for e in query.entities):
        # Internal retrieval query, separate from the original user analysis.
        query = baseline.analyze(f"{query.input.raw_text} à {city_entity.text}")
    payload = query.model_dump(mode="json", by_alias=True)
    payload["intent"] = {"label": "pharmacy_info_location", "confidence": 0.0}
    payload["contains_out_of_scope_request"] = False
    payload["input"]["language"] = current.input.language
    payload["pharmacy_query"] = {
        "needs_pharmacy_info": True,
        "info_type": "location",
        "location_text": city_entity.text if city_entity else None,
    }
    analysis = AnalysisResponse.model_validate(payload)
    result = present_answer(analysis, location)
    language = current.input.language
    result["language"] = language
    city = next((p["city"] for p in result["pharmacies"] if p["city"]), None)
    prefix = (
        f"Voici les pharmacies enregistrées à {city}. Sans votre position précise, "
        "je ne peux pas les classer par distance depuis votre quartier."
        if city and location is None
        else ""
    )
    if language in {"ar", "darija_ar"} and city and location is None:
        prefix = (
            f"هذه صيدليات مسجلة في {city}. "
            "من دون موقعك الدقيق لا يمكن ترتيبها حسب قربها من الحي."
        )
    elif language == "darija_latn" and city and location is None:
        prefix = (
            f"Hado pharmacies msajjelin f {city}. "
            "Bla position precise ma n9derch nrtebhom 7sab l9orb men l7ay dyalek."
        )
    if prefix:
        result["answer"] = prefix + "\n\n" + result["answer"]
    if medicine_search:
        medicines = ", ".join(
            e.text for e in current.entities if e.type == "MEDICATION"
        )
        result["answer"] = (
            MESSAGES.get(language, MESSAGES["fr"])["availability"].format(
                meds=medicines
            )
            + "\n\n"
            + result["answer"]
        )
    elif medical:
        result["answer"] = present_answer(current)["answer"] + "\n\n" + result["answer"]
    help_text = PRESENTATION_HELP.get(language, PRESENTATION_HELP["fr"])
    if location is None and not any(
        a["type"] == "share_location" for a in result["actions"]
    ):
        result["actions"].append(
            {"type": "share_location", "label": help_text["share"]}
        )
    result["sources"] = [
        {
            "id": p["id"],
            "title": p["name"] or "Pharmacie",
            "url": url,
            "kind": "directory",
        }
        for p in result["pharmacies"]
        for url in p["source_urls"][:1]
    ]
    # No saved named match in the resolved city: use attributed enrichment only.
    names = [e.text for e in query.entities if e.type == "PHARMACY_NAME"]
    if names and city_entity and not result["pharmacies"]:
        from pharma_assistant.nlp.pharmacy_web import cached_contact

        saved = cached_contact(
            {"kind": "contact", "name": names[0], "city": city_entity.text}
        )
        if saved:
            result.update(saved)
            result["answer"] = (
                "Je ne dispose pas du stock en direct de cette pharmacie.\n\n"
                if medicine_search or medical
                else ""
            ) + saved["answer"]
    if names and not city_entity and location is None:
        result["answer"] = "Dans quelle ville se trouve cette pharmacie ?"
        result["pharmacies"] = []
        result["sources"] = []
    if medicine_search and not city_entity and location is None and not names:
        result["answer"] = (
            "Dans quelle ville ou quel quartier cherchez-vous ce médicament ?"
        )
        result["pharmacies"] = []
        result["sources"] = []
    return {"wanted": wanted, "result": result, "query": query.input.raw_text}
