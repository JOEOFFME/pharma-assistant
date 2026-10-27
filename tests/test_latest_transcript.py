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


def test_stock_request_keeps_rabat_not_same_named_pharmacies_elsewhere(pipeline):
    from pharma_assistant.api.chat_context import directory_context

    history = [{"role": "user", "text": "Rabat"}]
    result = directory_context(
        pipeline,
        "Est-ce que la pharmacie Al Irfane a du Panadol en stock maintenant ?",
        history,
    )
    assert result["wanted"]
    assert "Oujda" not in result["result"]["answer"]
    assert "Fès" not in result["result"]["answer"]
    assert "Rabat" in result["result"]["answer"]
    assert "stock" in result["result"]["answer"]
    assert all(p["city"] == "Rabat" for p in result["result"]["pharmacies"])


def test_panadol_search_inherits_city_without_inheriting_pharmacy_name(pipeline):
    from pharma_assistant.api.chat_context import directory_context

    result = directory_context(pipeline, "Où puis-je chercher du Panadol ?", HISTORY)
    assert result["wanted"]
    assert result["result"]["pharmacies"]
    assert all(p["city"] == "Rabat" for p in result["result"]["pharmacies"])
    assert "général" not in result["result"]["answer"]


def test_panadol_search_without_city_asks_for_it(pipeline):
    from pharma_assistant.api.chat_context import directory_context

    result = directory_context(pipeline, "Où puis-je chercher du Panadol ?")
    assert result["wanted"]
    assert "ville" in result["result"]["answer"]
    assert not result["result"]["pharmacies"]


def test_dosage_followup_explains_box_field_without_inference(pipeline):
    from pharma_assistant.api.price_clarification import presentation_followup

    question = clarify_price("prix amoxiline")["answer"]
    result = presentation_followup("dosage", [{"role": "assistant", "text": question}])
    assert "sur la boîte" in result["answer"]
    assert "pas de la quantité à prendre" in result["answer"]
    assert presentation_followup("dosage", []) is None
    assert (
        presentation_followup(
            "combien dois-je prendre ?", [{"role": "assistant", "text": question}]
        )
        is None
    )


def test_price_clarification_does_not_claim_first_brand_is_requested():
    result = clarify_price("prix amoxiline")
    assert "DISPAMOX" not in result["sources"][0]["title"]


def test_subsequent_directory_tool_retains_resolved_city(pipeline):
    from pharma_assistant.nlp.agent import PharmacyTools

    tools = PharmacyTools(pipeline)
    tools.city = "Rabat"
    result = tools.call("search_pharmacies", {"query": "pharmacie Al Irfane"})
    assert all(p["city"] == "Rabat" for p in result["pharmacies"])
    assert not any(p["city"] == "Oujda" for p in result["pharmacies"])


@pytest.mark.parametrize(
    "text",
    [
        "Où puis-je chercher du Panadol ?",
        "Est-ce que la pharmacie Al Irfane a du Panadol en stock maintenant ?",
    ],
)
def test_latest_finding_requests_return_local_evidence_on_outage(
    pipeline, monkeypatch, text
):
    monkeypatch.setenv("ASSISTANT_AGENT", "true")
    monkeypatch.setattr(
        "pharma_assistant.nlp.agent.run_agent",
        lambda *a, **k: (_ for _ in ()).throw(OSError("simulated outage")),
    )
    result = answer_from_data(
        OpenRouterPipeline(pipeline, PROVIDER),
        pipeline.analyze(text),
        text,
        history=[{"role": "user", "text": "Rabat"}],
    )
    assert "Rabat" in result["answer"]
    assert "Oujda" not in result["answer"]
    assert "traitement personnel" not in result["answer"]


def test_named_stock_without_city_asks_instead_of_mixing_cities(pipeline):
    from pharma_assistant.api.chat_context import directory_context

    result = directory_context(
        pipeline, "Est-ce que la pharmacie Al Irfane a du Panadol en stock maintenant ?"
    )
    assert not result["result"]["pharmacies"]
    assert "ville" in result["result"]["answer"]
    assert "Oujda" not in result["result"]["answer"]
