"""Exact user transcript: fax roles, topic changes and ambiguous misspelled prices."""

from datetime import date

import pytest

from pharma_assistant.api.data_chat import answer_from_data
from pharma_assistant.api.price_clarification import clarify_price
from pharma_assistant.data.cnops import lookup
from pharma_assistant.nlp.agent import OpenRouterProvider
from pharma_assistant.nlp.openrouter import OpenRouterPipeline
from pharma_assistant.nlp.pharmacy_web import (
    contact_phones,
    lookup_request,
    source_period_matches,
)

PROVIDER = OpenRouterProvider("test-only", "openai/gpt-4.1")
REQUEST = {"name": "Al Irfane", "city": "Rabat"}
HISTORY = [
    {"role": "user", "text": "Je veux le contact de la pharmacie Al Irfane à Rabat."},
    {"role": "assistant", "text": "Pharmacie Al Irfane — téléphone publié."},
    {
        "role": "user",
        "text": "Cherche les pharmacies de garde à Rabat pour cette semaine.",
    },
    {"role": "assistant", "text": "Aucun planning vérifiable."},
]


def test_telecontact_phone_and_fax_are_not_merged():
    source = {
        "excerpt": (
            "Pharmacie Elirfane Rabat\nTel 1: 05 37 68 63 17\n" "Fax: 05 37 77 02 40"
        )
    }
    assert contact_phones(source, REQUEST) == {"+212537686317"}


def test_sibling_pharmacies_and_footer_phones_are_not_merged():
    source = {
        "excerpt": (
            "Pharmacie El Irfane Rabat\n+212.537.68.63.17\n"
            "List of Pharmacies in Rabat\nPharmacie Azhar\n"
            "+212.537.68.08.17\nNos services\n0522777111"
        )
    }
    assert contact_phones(source, REQUEST) == {"+212537686317"}


@pytest.mark.parametrize(
    "text",
    [
        "fin nl9a pandol f rabat",
        "ch7al prix dyal amoxiline",
        "je veux le prix d'amoxiline au maroc",
    ],
)
def test_new_request_does_not_replay_the_old_contact(pipeline, text):
    assert lookup_request(pipeline, text, HISTORY) is None


def test_only_an_immediate_location_statement_continues_contact(pipeline):
    history = HISTORY[:2]
    request = lookup_request(pipeline, "je suis a rabat madiant al Irafen", history)
    assert request["kind"] == "contact" and request["name"] == "Al Irfane"
    assert lookup_request(pipeline, "Rabat Al Irfane", HISTORY) is None


@pytest.mark.parametrize(
    "text", ["ch7al prix dyal amoxiline", "je veux le prix d'amoxiline au maroc"]
)
def test_misspelling_is_a_reference_candidate_not_a_guessed_price(
    pipeline, monkeypatch, text
):
    result = lookup(text)
    assert result["corrections"][0]["candidate"] == "amoxicilline"
    assert result["corrections"][0]["needs_confirmation"]
    assert result["presentation_ambiguous"]
    monkeypatch.setenv("ASSISTANT_AGENT", "true")
    monkeypatch.setenv("ASSISTANT_WEB_FIRST", "true")

    def unavailable(*a, **k):
        raise OSError()

    monkeypatch.setattr("pharma_assistant.nlp.agent.run_agent", unavailable)
    response = answer_from_data(
        OpenRouterPipeline(pipeline, PROVIDER),
        pipeline.analyze(text),
        text,
        history=HISTORY,
    )
    assert response["answer_source"] == "medicine_price_clarification"
    assert "amoxicilline" in response["answer"]
    assert "dosage" in response["answer"]
    assert "?" in response["answer"]
    assert "Je n’ai pas pu" not in response["answer"]
    assert not response["pharmacies"]


def test_generic_model_failure_text_is_repaired_to_a_price_clarification(
    pipeline, monkeypatch
):
    monkeypatch.setenv("ASSISTANT_AGENT", "true")
    monkeypatch.setattr(
        "pharma_assistant.nlp.agent.run_agent",
        lambda *a, **k: {
            "answer": "Je n’ai pas pu vérifier cette information. Réessayez.",
            "model": "fake",
            "pharmacies": [],
        },
    )
    text = "ch7al prix dyal amoxiline"
    response = answer_from_data(
        OpenRouterPipeline(pipeline, PROVIDER), pipeline.analyze(text), text
    )
    assert response["answer_source"] == "medicine_price_clarification"


def test_requested_price_comparison_is_left_to_agent():
    assert clarify_price("Compare les prix des présentations d’amoxicilline") is None


def test_duty_week_range_with_shared_year_is_understood():
    text = "Pharmacies de garde à Rabat du lundi 26 octobre – lundi 2 novembre 2026"
    assert source_period_matches(text, date(2026, 10, 26), date(2026, 11, 1))
    assert not source_period_matches(text, date(2026, 11, 9), date(2026, 11, 15))


def test_a_brand_price_question_keeps_its_brand():
    answer = clarify_price("Quel est le prix de Panadol ?")["answer"]
    assert "PANADOL" in answer
    assert "PARACETAMOL" not in answer


def test_helpful_model_clarification_is_not_replaced_by_old_city_contacts(
    pipeline, monkeypatch
):
    monkeypatch.setenv("ASSISTANT_AGENT", "true")
    monkeypatch.setattr(
        "pharma_assistant.nlp.agent.run_agent",
        lambda *a, **k: {
            "answer": "Quelle forme et quelle boîte d’amoxicilline cherchez-vous ?",
            "model": "fake",
            "pharmacies": [],
            "answer_source": "openrouter_agent",
            "web_search": {"attempted": True, "succeeded": False},
        },
    )
    text = "prix amoxicilline"
    result = answer_from_data(
        OpenRouterPipeline(pipeline, PROVIDER),
        pipeline.analyze(text),
        text,
        history=HISTORY,
    )
    assert "Quelle forme" in result["answer"]
    assert result["answer_source"] == "openrouter_agent"
    assert not result["pharmacies"]


def test_shared_year_start_date_can_be_cited_without_fabricating_year():
    from pharma_assistant.nlp.pharmacy_web import dates

    assert date(2026, 10, 26) in dates("du 26 octobre – 2 novembre 2026")
