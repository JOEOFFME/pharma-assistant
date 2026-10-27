"""Reported short questions produce bounded sourced answers without fake research."""

import pytest

from pharma_assistant.api.data_chat import answer_from_data
from pharma_assistant.api.reply_policy import short_reply, validate_search_attribution
from pharma_assistant.nlp.openrouter import OpenRouterPipeline, OpenRouterProvider


def test_exact_reported_example_is_one_sourced_name_not_a_model_essay(
    pipeline, monkeypatch
):
    monkeypatch.setenv("ASSISTANT_AGENT", "true")
    monkeypatch.setattr(
        "pharma_assistant.nlp.agent.run_agent",
        lambda *a, **k: pytest.fail("No model essay needed"),
    )
    question = (
        "Donne-moi un exemple de médicament utilisé contre les crises "
        "de migraine, à titre informatif."
    )
    engine = OpenRouterPipeline(
        pipeline, OpenRouterProvider("test-only", "openai/gpt-4.1")
    )
    result = answer_from_data(engine, pipeline.analyze(question), question)
    assert result["answer_source"] == "saved_health_reference"
    assert "sumatriptan" in result["answer"]
    assert "ibuprofène" not in result["answer"]
    assert "Voulez-vous" not in result["answer"]
    assert len(result["answer"]) < 230
    assert result["sources"]
    assert result["model"] is None


def test_exact_panadol_question_asks_only_missing_place(pipeline, monkeypatch):
    monkeypatch.setenv("ASSISTANT_AGENT", "true")
    monkeypatch.setattr(
        "pharma_assistant.nlp.agent.run_agent",
        lambda *a, **k: pytest.fail("Ask for city before research"),
    )
    question = "Où puis-je chercher du Panadol ?"
    engine = OpenRouterPipeline(
        pipeline, OpenRouterProvider("test-only", "openai/gpt-4.1")
    )
    result = answer_from_data(engine, pipeline.analyze(question), question)
    assert (
        result["answer"]
        == "Dans quelle ville ou quel quartier cherchez-vous « Panadol » ?"
    )
    assert not result["sources"]
    assert result["answer_source"] == "location_clarification"


def test_prior_user_city_is_not_lost_by_short_answer_policy(pipeline):
    question = "Où puis-je chercher du Doliprane ?"
    history = [{"role": "user", "text": "Je suis à Rabat"}]
    assert (
        short_reply(pipeline, pipeline.analyze(question), question, history=history)
        is None
    )


@pytest.mark.parametrize(
    "question",
    [
        "Quel dosage de sumatriptan prendre pour ma migraine ?",
        "Cherche sur le web un exemple de médicament contre la migraine.",
    ],
)
def test_personal_dosing_and_explicit_web_requests_are_not_canned_examples(
    pipeline, question
):
    assert short_reply(pipeline, pipeline.analyze(question), question) is None


@pytest.mark.parametrize(
    "answer",
    [
        "Je n'ai pas pu vérifier le Panadol à partir de cette recherche.",
        "J’ai consulté le web pour cette demande.",
        "Après une recherche, voici le résultat.",
    ],
)
def test_claimed_research_requires_an_actual_successful_tool(answer):
    with pytest.raises(ValueError):
        validate_search_attribution(answer, False)
    validate_search_attribution(answer, True)


def test_explicit_saved_directory_lookup_is_not_claimed_as_web():
    validate_search_attribution("J’ai consulté l’annuaire enregistré.", False)


def test_new_medicine_topic_does_not_reuse_old_migraine_reference(pipeline):
    question = "bghit ghir smya dyalo"
    history = [
        {"role": "user", "text": "Un médicament pour la migraine ?"},
        {"role": "user", "text": "Où chercher du Panadol ?"},
    ]
    assert short_reply(pipeline, pipeline.analyze(question), question, history) is None


@pytest.mark.parametrize(
    "question",
    [
        "Donne-moi un exemple de médicament qui ne traite pas la migraine.",
        "Quel est le nom d'un médecin spécialisé dans la migraine ?",
    ],
)
def test_other_or_negative_example_requests_are_not_replaced(pipeline, question):
    assert short_reply(pipeline, pipeline.analyze(question), question) is None
