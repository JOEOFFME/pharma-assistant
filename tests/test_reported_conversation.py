"""The reported Rabat/migraine conversation remains useful during provider failures."""

import pytest

from pharma_assistant.api.chat_context import directory_context
from pharma_assistant.api.data_chat import (
    answer_from_data,
    retrieved_context,
    validate_reply,
)
from pharma_assistant.nlp.openrouter import (
    GroundedReply,
    OpenRouterPipeline,
    OpenRouterProvider,
)

PROVIDER = OpenRouterProvider("test-only-key", "openai/gpt-4.1")
HISTORY = [
    {"role": "user", "text": "ou je peux trouver pres de moi le paracétamol"},
    {"role": "assistant", "text": "Pouvez-vous préciser votre ville ou quartier ?"},
    {"role": "user", "text": "je suis a rabat madinat al irfane"},
    {"role": "assistant", "text": "Voulez-vous les coordonnées de pharmacies ?"},
]


def no_model(*a, **k):
    raise OSError("test-only provider outage")


@pytest.mark.parametrize(
    "text,history",
    [
        ("je suis a rabat madinat al irfane", HISTORY[:2]),
        ("Rabat AL Irfane", HISTORY),
        ("oui", HISTORY),
        ("Je voudrais 2 boîtes de Doliprane 1000 mg en comprimés.", HISTORY),
    ],
)
def test_reported_location_confirmation_and_request_keep_real_results_on_outage(
    pipeline, monkeypatch, text, history
):
    monkeypatch.setenv("ASSISTANT_AGENT", "true")
    monkeypatch.setattr("pharma_assistant.nlp.agent.run_agent", no_model)
    result = answer_from_data(
        OpenRouterPipeline(pipeline, PROVIDER),
        pipeline.analyze(text),
        text,
        history=history,
    )
    assert result["answer_source"] == "local_directory"
    assert result["pharmacies"]
    assert all(p["city"] == "Rabat" for p in result["pharmacies"])
    assert result["pharmacies"][0]["name"] in result["answer"]
    assert result["sources"][0]["url"].startswith("https://www.openstreetmap.org/")
    assert "classer par distance" in result["answer"]
    assert "Je n’ai pas pu vérifier" not in result["answer"]
    assert any(a["type"] == "share_location" for a in result["actions"])
    if "Doliprane" in text:
        assert "1000 mg" in result["answer"]
        assert "2 boîtes" in result["answer"]
        assert "comprimés" in result["answer"]


def test_unrelated_question_or_negative_does_not_replay_old_location(pipeline):
    assert not directory_context(pipeline, "non merci", HISTORY)["wanted"]
    assert not directory_context(
        pipeline, "Quelle est la capitale du Canada ?", HISTORY
    )["wanted"]


@pytest.mark.parametrize(
    "style", ["1. {name} — Rabat.", "3tini ma3loumat 3la {name}, f Rabat."]
)
def test_numbered_lists_and_arabizi_are_not_invented_numbers(pipeline, style):
    context, rows = retrieved_context(pipeline.analyze("Rabat"))
    answer = style.format(name=rows[0]["name"])
    validate_reply(
        GroundedReply(
            answer=answer,
            source_ids=[rows[0]["id"]],
            stock_status="unverified",
            duty_status="unverified",
            medical_refusal=False,
        ),
        context,
        "Rabat",
    )


def test_invented_actual_numbers_are_still_rejected(pipeline):
    context, rows = retrieved_context(pipeline.analyze("Rabat"))
    with pytest.raises(ValueError, match="numeric"):
        validate_reply(
            GroundedReply(
                answer=rows[0]["name"] + " — 99999 km.",
                source_ids=[rows[0]["id"]],
                stock_status="unverified",
                duty_status="unverified",
                medical_refusal=False,
            ),
            context,
            "Rabat",
        )


def test_preloaded_directory_prevents_a_second_permission_loop(pipeline, monkeypatch):
    monkeypatch.setenv("ASSISTANT_AGENT", "true")
    monkeypatch.setattr(
        "pharma_assistant.nlp.agent.run_agent",
        lambda *a, **k: {
            "answer": "Voulez-vous que je recherche cela ?",
            "pharmacies": [],
            "model": "fake-model",
        },
    )
    result = answer_from_data(
        OpenRouterPipeline(pipeline, PROVIDER),
        pipeline.analyze("oui"),
        "oui",
        history=HISTORY,
    )
    assert result["pharmacies"]
    assert "Voulez-vous" not in result["answer"]


@pytest.mark.parametrize(
    "text,language",
    [
        ("bghit smiya dyal dwa dyal la migraine", "darija_latn"),
        ("le nom d'un medicament pour traitement de la migraine", "fr"),
    ],
)
def test_migraine_name_has_attributed_saved_reference_during_outage(
    pipeline, monkeypatch, text, language
):
    monkeypatch.setenv("ASSISTANT_AGENT", "true")
    monkeypatch.setattr("pharma_assistant.nlp.agent.run_agent", no_model)
    result = answer_from_data(
        OpenRouterPipeline(pipeline, PROVIDER),
        pipeline.analyze(text, language_hint=language),
        text,
    )
    assert result["answer_source"] == "saved_health_reference"
    assert "sumatriptan" in result["answer"].casefold()
    assert all(s["url"].startswith("https://www.nhs.uk/") for s in result["sources"])
    assert "référence" in result["answer"]
    assert "Je n’ai pas pu vérifier" not in result["answer"]


def test_reported_unsourced_treatment_list_cannot_pass_as_clarification(
    pipeline, monkeypatch
):
    import json

    from pharma_assistant.nlp.agent import run_agent

    body = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "answer": (
                                "Je ne peux pas vérifier les noms.\n"
                                "- paracétamol\n- ibuprofène\n- sumatriptan"
                            ),
                            "source_ids": [],
                            "kind": "clarification",
                        }
                    )
                }
            }
        ]
    }
    monkeypatch.setattr("pharma_assistant.nlp.agent.chat", lambda *a, **k: body)
    with pytest.raises(ValueError, match="Unsourced"):
        run_agent(PROVIDER, pipeline, "nom de médicament pour la migraine", "fr")


def test_numeric_phone_formatting_preserves_real_number(pipeline):
    context = {
        "pharmacies": [
            {"id": "source", "name": "Source pharmacy", "phones": ["+212537675669"]}
        ]
    }
    validate_reply(
        GroundedReply(
            answer="1. Source pharmacy — +212 537 675669",
            source_ids=["source"],
            stock_status="unverified",
            duty_status="unverified",
            medical_refusal=False,
        ),
        context,
        "Téléphone ?",
    )


def test_diagnostic_codes_do_not_echo_provider_error_bodies():
    from pharma_assistant.nlp.agent import failure_code

    assert (
        failure_code(ValueError("secret content must not appear"))
        == "provider_or_validation_failure"
    )
    assert (
        failure_code(ValueError("Unsupported numeric claim"))
        == "unsupported_numeric_claim"
    )
