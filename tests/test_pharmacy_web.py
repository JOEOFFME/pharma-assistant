"""Business web requests use the network tool and cannot become a generic OSM list."""

from datetime import date

import pytest

from pharma_assistant.api.chat_context import directory_context
from pharma_assistant.api.data_chat import answer_from_data
from pharma_assistant.nlp.agent import OpenRouterProvider, PharmacyTools, run_agent
from pharma_assistant.nlp.openrouter import OpenRouterPipeline
from pharma_assistant.nlp.pharmacy_web import lookup_request

PROVIDER = OpenRouterProvider("test-only", "openai/gpt-4.1")
HISTORY = [{"role": "user", "text": "ou je peux trouver Panadol sur Rabat ?"}]
CONTACT_URL = (
    "https://www.santeservice.ma/pharmacies-de-garde/rabat/pharmacie-el-irfane.html"
)
DUTY_URL = "https://www.guidepharmacies.ma/pharmacies-de-garde/rabat.html"


def research(excerpt, summary="Pharmacie El Irfane — 0537 68 63 17", url=CONTACT_URL):
    return {
        "choices": [
            {
                "message": {
                    "content": summary,
                    "annotations": [
                        {
                            "type": "url_citation",
                            "url_citation": {
                                "url": url,
                                "title": "Published pharmacy source",
                                "content": excerpt,
                            },
                        }
                    ],
                }
            }
        ]
    }


def test_named_contact_really_calls_business_web_and_is_not_overwritten(
    pipeline, monkeypatch
):
    monkeypatch.setenv("ASSISTANT_AGENT", "true")
    bodies = []

    def transport(provider, body, timeout):
        bodies.append(body)
        return research(
            "Pharmacie EL IRFANE, Rabat — Campus Madinat Al Irfane. Tél: 0537 68 63 17"
        )

    monkeypatch.setattr("pharma_assistant.nlp.agent.chat", transport)
    text = "je veux le contact de pharmacy Al Irfane"
    result = answer_from_data(
        OpenRouterPipeline(pipeline, PROVIDER),
        pipeline.analyze(text),
        text,
        history=HISTORY,
    )
    assert result["answer_source"] == "pharmacy_web"
    assert "+212537686317" in result["answer"]
    assert result["pharmacies"] == []
    assert result["tools_used"] == ["search_pharmacy_web"]
    assert result["web_search"] == {
        "attempted": True,
        "retrieved": True,
        "succeeded": True,
    }
    assert "santeservice.ma" in bodies[0]["plugins"][0]["include_domains"]
    assert "Rabat" in bodies[0]["messages"][-1]["content"]
    assert directory_context(pipeline, text, HISTORY) is None


def test_location_reply_keeps_named_contact_not_generic_city(pipeline):
    history = HISTORY + [
        {"role": "user", "text": "je veux le contact de pharmacy Al Irfane"}
    ]
    request = lookup_request(pipeline, "je suis a rabat madiant al Irafen", history)
    assert request["name"] == "Al Irfane"
    assert request["city"].casefold() == "rabat"
    assert request["kind"] == "contact"


def test_weekly_duty_really_searches_date_range_and_returns_source(
    pipeline, monkeypatch
):
    monkeypatch.setattr(
        "pharma_assistant.nlp.pharmacy_web.today", lambda: date(2026, 10, 27)
    )
    bodies = []

    def transport(provider, body, timeout):
        bodies.append(body)
        return research(
            (
                "Rabat — Pharmacies de garde. Mardi 27 octobre 2026. "
                "Pharmacie IBN HAJAR 0537 68 06 87."
            ),
            "Pharmacie IBN HAJAR — 27/10/2026 — 0537 68 06 87.",
            DUTY_URL,
        )

    monkeypatch.setattr("pharma_assistant.nlp.agent.chat", transport)
    result = run_agent(
        PROVIDER,
        pipeline,
        "chercher les pharmacies de gardes pour cette semaine",
        "fr",
        history=HISTORY,
    )
    assert result["answer_source"] == "pharmacy_web"
    assert "2026-10-26" in bodies[0]["messages"][-1]["content"]
    assert "2026-11-01" in bodies[0]["messages"][-1]["content"]
    assert "IBN HAJAR" in result["answer"]
    assert result["sources"][0]["url"] == DUTY_URL
    assert not result["pharmacies"]


@pytest.mark.parametrize(
    "excerpt",
    [
        "Rabat Pharmacie de garde 27 octobre 2024. Pharmacie IBN HAJAR 0537 68 06 87.",
        "Rabat Pharmacie IBN HAJAR — Horaires habituels 24h/24.",
        "Casablanca Pharmacie de garde 27 octobre 2026. 0537 68 06 87.",
    ],
)
def test_stale_undated_or_wrong_city_cannot_be_a_weekly_duty_answer(
    pipeline, monkeypatch, excerpt
):
    monkeypatch.setattr(
        "pharma_assistant.nlp.pharmacy_web.today", lambda: date(2026, 10, 27)
    )
    monkeypatch.setattr(
        "pharma_assistant.nlp.agent.chat",
        lambda *a, **k: research(excerpt, url=DUTY_URL),
    )
    result = run_agent(
        PROVIDER, pipeline, "pharmacies de garde cette semaine", "fr", history=HISTORY
    )
    assert result["answer_source"] == "web_lookup_unavailable"
    assert not result["web_search"]["succeeded"]
    assert result["sources"]
    assert result["web_search"]["retrieved"] is True
    assert "Benyahya" not in result["answer"]


def test_search_outage_returns_only_verified_named_contact_cache(pipeline, monkeypatch):
    def failure(*a, **k):
        raise OSError("offline")

    monkeypatch.setattr("pharma_assistant.nlp.agent.chat", failure)
    result = run_agent(
        PROVIDER, pipeline, "contact de pharmacy Al Irfane", "fr", history=HISTORY
    )
    assert result["answer_source"] == "saved_contact"
    assert "+212537686317" in result["answer"]
    assert "Source enregistrée" in result["answer"]
    assert result["web_search"] == {
        "attempted": True,
        "retrieved": False,
        "succeeded": False,
    }
    assert not result["pharmacies"]


def test_wrong_city_contact_is_not_used_or_cached(pipeline, monkeypatch):
    monkeypatch.setattr(
        "pharma_assistant.nlp.agent.chat",
        lambda *a, **k: research("Al Irfane Fès 0535 61 08 27"),
    )
    result = run_agent(PROVIDER, pipeline, "contact de pharmacy Al Noor à Rabat", "fr")
    assert result["answer_source"] == "web_lookup_unavailable"
    assert "0535" not in result["answer"]


def test_contact_without_city_asks_city_and_never_guesses(pipeline, monkeypatch):
    monkeypatch.setattr(
        "pharma_assistant.nlp.agent.chat",
        lambda *a, **k: pytest.fail("No city: do not search"),
    )
    result = run_agent(PROVIDER, pipeline, "contact de pharmacy Al Irfane", "fr")
    assert result["answer_source"] == "clarification"
    assert not result["web_search"]["attempted"]


def test_disabled_web_is_not_advertised_or_reported_successful(pipeline, monkeypatch):
    monkeypatch.setenv("ASSISTANT_WEB_SEARCH", "false")
    tools = PharmacyTools(pipeline, PROVIDER)
    assert "search_pharmacy_web" not in {d["name"] for d in tools.definitions()}
    result = run_agent(
        PROVIDER, pipeline, "contact de pharmacy Al Irfane à Rabat", "fr"
    )
    assert result["answer_source"] == "saved_contact"
    assert result["web_search"] == {
        "attempted": False,
        "retrieved": False,
        "succeeded": False,
    }
