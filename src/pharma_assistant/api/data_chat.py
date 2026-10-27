"""Retrieval-augmented main OpenRouter conversation with local evidence checks."""

import json
import logging
import os
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
    # List labels and Arabizi letters are formatting/language, not numeric facts.
    checked = re.sub(r"(?m)^\s*\(?\d+[.)]\s+", "", reply.answer)
    for fact in facts:
        for phone in fact.get("phones", []):
            digits = re.sub(r"\D", "", phone)
            if digits:
                pattern = r"(?<!\d)\+?" + r"[\s().-]*".join(digits) + r"(?!\d)"
                checked = re.sub(pattern, "", checked)
    actual_numbers = set(re.findall(r"(?<!\w)\d+(?!\w)", checked))
    if not actual_numbers <= allowed_numbers:
        raise ValueError("Unsupported numeric claim")
    validate_live_claims(reply.answer)


def validate_live_claims(answer: str, allow_general_existence: bool = False) -> None:
    """Reject common unsupported stock and current-duty assertions in any chat mode."""
    for sentence in re.split(r"[.!\n]", answer.casefold()):
        if "?" in sentence or re.search(
            r"\b(?:pas|non|sans|cannot|not|unverified|inconnu|inconnue|impossible)\b"
            r"|n.ai|ne peux|ma 3ndich|ma n9der|غير|لا |ليست|ما عند",
            sentence,
        ):
            continue
        pattern = (
            r"\b(?:en stock|de garde|open now|ouvert maintenant"
            r"|available at|disponible (?:chez|à|a)|disponibles (?:chez|à|a))\b"
            r"|مناوبة|متوفر في|كاين فالصيدلية"
            if allow_general_existence
            else r"\b(?:disponible|disponibles|available|kayn|kayna|en stock"
            r"|de garde|open now|ouvert maintenant)\b|متوفر|كاين|مناوبة"
        )
        if re.search(pattern, sentence):
            raise ValueError("Unsupported stock/duty/open-now claim")


def answer_from_data(engine, analysis, text, location=None, history=None) -> dict:
    """OpenRouter writes the main answer; local fallback is explicit on failure."""
    fallback = present_answer(analysis, location)
    if (
        os.getenv("ASSISTANT_AGENT", "true").lower() == "true"
        and os.getenv("ASSISTANT_WEB_FIRST", "true").lower() != "true"
    ):
        from pharma_assistant.api.reply_policy import short_reply

        direct = short_reply(
            getattr(engine, "baseline", engine), analysis, text, history, location
        )
        if direct:
            return {**fallback, **direct}
    provider = getattr(engine, "provider", None)
    if provider is None:
        return {**fallback, "answer_source": "local_directory", "model": None}
    if os.getenv("ASSISTANT_AGENT", "true").lower() == "true":
        from pharma_assistant.api.chat_context import directory_context
        from pharma_assistant.nlp.agent import failure_code, run_agent

        directory = directory_context(engine.baseline, text, history, location)
        try:
            result = run_agent(
                provider,
                engine.baseline,
                text,
                analysis.input.language,
                history=history,
                location=location,
            )
            researched = (
                os.getenv("ASSISTANT_WEB_FIRST", "true").lower() == "true"
                and result.get("web_search", {}).get("succeeded") is True
            )
            if (
                directory
                and directory["wanted"]
                and directory["result"]["pharmacies"]
                and not researched
            ):
                # Keep available records instead of asking permission to search again.
                if not result.get("pharmacies") or not any(
                    p["name"] and p["name"] in result["answer"]
                    for p in directory["result"]["pharmacies"]
                ):
                    return {
                        **directory["result"],
                        "analysis": fallback["analysis"],
                        "answer_source": "local_directory",
                        "model": None,
                    }
            return {**fallback, **result}
        except (ValueError, OSError) as error:
            logger.warning(
                "Agent fallback: code=%s, type=%s",
                failure_code(error),
                type(error).__name__,
            )
            if directory and directory["wanted"]:
                return {
                    **directory["result"],
                    "analysis": fallback["analysis"],
                    "answer_source": "local_directory",
                    "model": None,
                    "fallback_reason": "agent_unavailable_or_invalid",
                }
            from pharma_assistant.nlp.health_reference import (
                reference_answer,
                reference_for,
            )

            reference = (
                None
                if os.getenv("ASSISTANT_WEB_FIRST", "true").lower() == "true"
                else reference_for(text, history)
            )
            if reference:
                return {
                    **fallback,
                    **reference_answer(reference, analysis.input.language),
                    "fallback_reason": "agent_unavailable_or_invalid",
                }
            language = analysis.input.language
            message = (
                "Ma 9dertch nverifi had lma3louma daba. T9der t3awed tjarreb; "
                "n9der n3awnek b ma3loumat 3amma 3la dwa bla ma nkhtar lik 3ilaj."
                if language == "darija_latn"
                else (
                    "تعذر التحقق من هذه المعلومة الآن. يمكنك المحاولة مجددًا. "
                    "يمكنني شرح معلومات عامة عن الأدوية دون اختيار علاج شخصي."
                    if language in {"ar", "darija_ar"}
                    else "Je n’ai pas pu vérifier cette information pour le moment. "
                    "Réessayez ; je peux expliquer les traitements en général, "
                    "sans choisir un traitement personnel."
                )
            )
            return {
                **fallback,
                "answer": message,
                "answer_source": "local_fallback",
                "model": None,
                "fallback_reason": "agent_unavailable_or_invalid",
            }
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
