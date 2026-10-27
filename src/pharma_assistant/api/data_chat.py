"""Retrieval-augmented main OpenRouter conversation with local evidence checks."""

import json
import logging
import re

from pharma_assistant.api.answers import MESSAGES, present_answer
from pharma_assistant.api.schemas import AnalysisResponse
from pharma_assistant.data.pharmacies import haversine_km
from pharma_assistant.nlp.intent import contains_medical_advice
from pharma_assistant.nlp.openrouter import GroundedReply, compose_reply

logger = logging.getLogger(__name__)


def retrieved_context(analysis: AnalysisResponse, location=None) -> tuple[dict, list]:
    """Retrieve relevant contacts for pharmacy and medicine questions."""
    payload = analysis.model_dump(mode="json", by_alias=True)
    locations = [
        e
        for e in analysis.entities
        if e.type == "LOCATION" and e.assertion == "affirmed"
    ]
    pharmacies = [
        e
        for e in analysis.entities
        if e.type == "PHARMACY_NAME" and e.assertion == "affirmed"
    ]
    records = []
    if locations or pharmacies or location is not None:
        payload["intent"] = {"label": "pharmacy_info_location", "confidence": 0.0}
        payload["pharmacy_query"] = {
            "needs_pharmacy_info": True,
            "info_type": "location",
            "location_text": locations[0].text if locations else None,
        }
        records = present_answer(AnalysisResponse.model_validate(payload), location)[
            "pharmacies"
        ]
    facts = [
        {
            "id": p["id"],
            "name": p["name"],
            "city": p["city"],
            "phones": p["phones_e164"],
            "recorded_hours": p["opening_hours"],
            "source_urls": p["source_urls"],
        }
        for p in records
    ]
    if location is not None:
        for fact, record in zip(facts, records, strict=True):
            distance = haversine_km(
                location.latitude,
                location.longitude,
                record["latitude"],
                record["longitude"],
            )
            fact["distance"] = f"{distance:.2f} km (à vol d’oiseau)"
    return {
        "pharmacies": facts,
        "requested_locations": [e.text for e in locations],
        "has_shared_location": location is not None,
        "live_stock": "unverified",
        "moroccan_prices": "unverified",
        "current_duty": "unverified",
        "coverage": "saved directory, incomplete",
        "medicine_mentions": [
            e.text
            for e in analysis.entities
            if e.type == "MEDICATION" and e.assertion == "affirmed"
        ],
    }, records


def validate_reply(reply: GroundedReply, context: dict, question: str) -> None:
    """Reject wrong citations, new numeric facts and common unsupported live claims."""
    if not reply.medical_refusal and re.search(
        r"\b(?:prenez|diagnostic|twice daily|fois par jour|nakhod|nakhdo)\b"
        r"|تناول|خذ جرعة",
        reply.answer.casefold(),
    ):
        raise ValueError("Unrequested clinical advice")
    sources = {p["id"]: p for p in context["pharmacies"]}
    if not set(reply.source_ids) <= sources.keys():
        raise ValueError("Unknown pharmacy citation")
    for identifier in reply.source_ids:
        name = sources[identifier]["name"]
        if name and name.casefold() not in reply.answer.casefold():
            raise ValueError("Cited pharmacy absent from answer")
    # Source IDs can contain arbitrary digits: do not treat them as factual numbers.
    facts = [
        {k: v for k, v in p.items() if k not in {"id", "source_urls"}}
        for p in context["pharmacies"]
    ]
    allowed_numbers = set(
        re.findall(r"\d+", json.dumps(facts, ensure_ascii=False) + question)
    )
    if not set(re.findall(r"\d+", reply.answer)) <= allowed_numbers:
        raise ValueError("Unsupported numeric claim")
    for sentence in re.split(r"[.!\n]", reply.answer.casefold()):
        if "?" in sentence or re.search(
            r"\b(?:pas|non|sans|cannot|not|unverified|inconnu|inconnue|impossible)\b"
            r"|n.ai|ne peux|ma 3ndich|ma n9der|غير|لا |ليست|ما عند",
            sentence,
        ):
            continue
        if re.search(
            r"\b(?:disponible|disponibles|available|kayn|kayna|en stock"
            r"|de garde|open now"
            r"|ouvert maintenant)\b|متوفر|كاين|مناوبة",
            sentence,
        ):
            raise ValueError("Unsupported stock/duty/open-now claim")


def answer_from_data(engine, analysis, text, location=None, history=None) -> dict:
    """OpenRouter writes the main answer; local fallback is explicit on failure."""
    fallback = present_answer(analysis, location)
    provider = getattr(engine, "provider", None)
    if provider is None:
        return {**fallback, "answer_source": "local_directory", "model": None}
    if (
        contains_medical_advice(text, engine.baseline.config)
        or analysis.contains_out_of_scope_request
    ):
        return {**fallback, "answer_source": "medical_boundary", "model": None}
    retrieval_analysis = analysis
    context, records = retrieved_context(analysis, location)
    if (
        not records
        and location is None
        and not any(e.type in {"LOCATION", "PHARMACY_NAME"} for e in analysis.entities)
    ):
        for turn in reversed(history or []):
            if turn["role"] != "user":
                continue
            previous = engine.baseline.analyze(turn["text"])
            if any(e.type in {"LOCATION", "PHARMACY_NAME"} for e in previous.entities):
                retrieval_analysis = previous
                context, records = retrieved_context(previous)
                break
    try:
        reply, model = compose_reply(
            provider, text, context, history or [], analysis.input.language
        )
        validate_reply(reply, context, text)
        answer = (
            MESSAGES.get(analysis.input.language, MESSAGES["fr"])["refusal"]
            if reply.medical_refusal
            else reply.answer
        )
        result = {
            **fallback,
            "answer": answer,
            "pharmacies": records,
            "answer_source": "openrouter_grounded",
            "model": model,
            "source_ids": reply.source_ids,
        }
        if records and not result["actions"]:
            result["actions"] = [
                {"type": "find_pharmacy", "label": "Voir les pharmacies"}
            ]
        return result
    except (ValueError, OSError) as error:
        logger.warning(
            "Main model fallback: %s, status=%s",
            type(error).__name__,
            getattr(error, "code", None),
        )
        if records:
            payload = retrieval_analysis.model_dump(mode="json", by_alias=True)
            payload["intent"] = {"label": "pharmacy_info_location", "confidence": 0.0}
            payload["pharmacy_query"] = {
                "needs_pharmacy_info": True,
                "info_type": "location",
                "location_text": (
                    context["requested_locations"][0]
                    if context["requested_locations"]
                    else None
                ),
            }
            directory = present_answer(
                AnalysisResponse.model_validate(payload), location
            )
            fallback["answer"] += "\n\n" + directory["answer"]
            fallback["pharmacies"] = records
        return {
            **fallback,
            "answer_source": "local_fallback",
            "model": None,
            "fallback_reason": "language_service_unavailable_or_invalid",
        }
