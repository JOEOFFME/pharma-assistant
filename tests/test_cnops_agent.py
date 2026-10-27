"""Real public CNOPS snapshot and mocked web-first agent transport."""

import hashlib
import json

import pytest

from pharma_assistant.api.data_chat import answer_from_data
from pharma_assistant.data.cnops import SNAPSHOT, records, search
from pharma_assistant.nlp.agent import (
    AgentReply,
    OpenRouterProvider,
    PharmacyTools,
    health_url,
    run_agent,
)
from pharma_assistant.nlp.cnops_policy import validate_cnops_claims
from pharma_assistant.nlp.openrouter import OpenRouterPipeline

PROVIDER = OpenRouterProvider("test-only", "openai/gpt-4.1")


def message(answer, ids, kind="information"):
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {"answer": answer, "source_ids": ids, "kind": kind}
                    )
                }
            }
        ],
        "model": "openai/gpt-4.1",
    }


def tool(name, query):
    return {
        "choices": [
            {
                "message": {
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": name,
                                "arguments": json.dumps({"query": query}),
                            },
                        }
                    ],
                }
            }
        ]
    }


def web(url, excerpt):
    return {
        "choices": [
            {
                "message": {
                    "content": excerpt,
                    "annotations": [
                        {
                            "type": "url_citation",
                            "url_citation": {
                                "url": url,
                                "title": "Official source",
                                "content": excerpt,
                            },
                        }
                    ],
                }
            }
        ]
    }


def test_actual_cnops_original_bytes_and_provenance_are_retained():
    metadata = json.loads((SNAPSHOT / "manifest.json").read_text())
    assert (
        hashlib.sha256((SNAPSHOT / "reference.xlsx").read_bytes()).hexdigest()
        == metadata["sha256"]
    )
    assert len(records()) == 5917
    assert metadata["source_updated"] == "2017-12-18"
    assert "2014" in metadata["edition"]
    assert metadata["license"] == "ODbL"


def test_actual_cnops_strength_equivalence_and_missing_name():
    rows = search("Doliprane 1000 mg comprimé")
    assert rows
    assert all(r["strength"] == "1" and r["strength_unit"] == "G" for r in rows)
    assert all("COMPRIME" in r["form"] for r in rows)
    assert search("brand_not_in_the_official_reference_123") == []
    assert all(r["name"] == "PANADOL" for r in search("Panadol"))


def test_cnops_tool_uses_official_web_domains_and_actual_snapshot(
    pipeline, monkeypatch
):
    bodies = []

    def transport(provider, body, timeout):
        bodies.append(body)
        return web(
            "https://cnops.org.ma/fr",
            "CNOPS médicament Panadol, consulter la présentation.",
        )

    monkeypatch.setattr("pharma_assistant.nlp.agent.chat", transport)
    registry = PharmacyTools(pipeline, PROVIDER)
    result = registry.call("search_cnops", {"query": "Panadol"})
    assert result["cnops_records"]
    assert all(r["historical"] for r in result["cnops_records"])
    assert set(bodies[0]["plugins"][0]["include_domains"]) == {
        "cnops.org.ma",
        "data.gov.ma",
    }
    assert registry.web_successes == 1


def test_failed_cnops_web_returns_dated_records_without_fake_success(
    pipeline, monkeypatch
):
    def failed(*a, **k):
        raise OSError()

    monkeypatch.setattr("pharma_assistant.nlp.agent.chat", failed)
    registry = PharmacyTools(pipeline, PROVIDER)
    result = registry.call("search_cnops", {"query": "Panadol"})
    assert result["cnops_records"]
    assert "web_error" in result
    assert registry.web_successes == 0
    assert all(r["kind"] == "cnops_record" for r in registry.sources.values())


def test_web_first_default_forces_a_research_tool_then_composes_from_cnops(
    pipeline, monkeypatch
):
    monkeypatch.delenv("ASSISTANT_WEB_FIRST", raising=False)
    row = search("Panadol")[0]
    answer = (
        f"CNOPS, référence historique 2014 : {row['name']}, "
        f"{row['presentation']}, PPV {row['ppv_mad']} MAD. "
        "Ce prix historique ne confirme pas le prix actuel."
    )
    responses = iter(
        [
            tool("search_cnops", "Panadol"),
            web("https://cnops.org.ma/fr", "Référentiel médicaments CNOPS."),
            message(answer, [row["id"]]),
        ]
    )
    bodies = []

    def transport(provider, body, timeout):
        bodies.append(body)
        return next(responses)

    monkeypatch.setattr("pharma_assistant.nlp.agent.chat", transport)
    result = run_agent(
        PROVIDER,
        pipeline,
        "Quel est le prix de ce médicament Panadol selon CNOPS ?",
        "fr",
    )
    assert bodies[0]["tool_choice"] == "required"
    assert {d["function"]["name"] for d in bodies[0]["tools"]} == {
        "search_cnops",
        "search_web",
        "search_health_web",
        "search_pharmacy_web",
    }
    assert result["model"] == "openai/gpt-4.1"
    assert result["web_search"]["succeeded"]
    assert result["sources"][0]["kind"] == "cnops_record"


def test_broad_general_question_uses_unrestricted_public_web(pipeline, monkeypatch):
    monkeypatch.setenv("ASSISTANT_WEB_FIRST", "true")
    responses = iter(
        [
            tool("search_web", "definition API documentation"),
            web(
                "https://developer.mozilla.org/en-US/docs/Glossary/API",
                "An API is a software interface.",
            ),
            message("Une API est une interface logicielle.", ["web:1:1"]),
        ]
    )
    bodies = []

    def transport(provider, body, timeout):
        bodies.append(body)
        return next(responses)

    monkeypatch.setattr("pharma_assistant.nlp.agent.chat", transport)
    result = run_agent(PROVIDER, pipeline, "Qu’est-ce qu’une API ?", "fr")
    assert "Une API" in result["answer"]
    assert "include_domains" not in bodies[1]["plugins"][0]
    assert result["sources"][0]["kind"] == "web_general"


def test_web_first_does_not_use_previous_canned_migraine_example(pipeline, monkeypatch):
    monkeypatch.setenv("ASSISTANT_WEB_FIRST", "true")
    monkeypatch.setenv("ASSISTANT_AGENT", "true")
    called = []

    def agent(*a, **k):
        called.append(True)
        return {
            "answer": "Réponse issue de la recherche du modèle.",
            "model": "test-model",
            "answer_source": "openrouter_agent",
            "sources": [],
        }

    monkeypatch.setattr("pharma_assistant.nlp.agent.run_agent", agent)
    question = "Donne-moi un exemple de médicament contre la migraine."
    result = answer_from_data(
        OpenRouterPipeline(pipeline, PROVIDER), pipeline.analyze(question), question
    )
    assert called and result["model"] == "test-model"
    assert result["answer_source"] == "openrouter_agent"


def test_required_research_cannot_be_ignored(pipeline, monkeypatch):
    monkeypatch.setenv("ASSISTANT_WEB_FIRST", "true")
    monkeypatch.setattr(
        "pharma_assistant.nlp.agent.chat",
        lambda *a, **k: message("Une réponse inventée.", [], kind="clarification"),
    )
    with pytest.raises(ValueError, match="Required research"):
        run_agent(PROVIDER, pipeline, "Quel est le prix de Panadol ?", "fr")


@pytest.mark.parametrize(
    "answer",
    [
        "Le prix actuel est 999.00 MAD.",
        "Référence 2014 : le prix est 999.00 MAD.",
    ],
)
def test_invented_or_undated_historical_amount_rejected(answer):
    row = search("Panadol")[0]
    source = {**row, "kind": "cnops_record"}
    reply = AgentReply(answer=answer, source_ids=[row["id"]], kind="information")
    with pytest.raises(ValueError):
        validate_cnops_claims(reply, {row["id"]: source}, True)


def test_foreign_reference_cannot_be_called_cnops_price_evidence():
    reply = AgentReply(
        answer="CNOPS : 42 MAD.", source_ids=["foreign"], kind="information"
    )
    with pytest.raises(ValueError, match="CNOPS evidence"):
        validate_cnops_claims(
            reply,
            {"foreign": {"url": "https://www.nhs.uk/", "kind": "web", "excerpt": "42"}},
            True,
        )


@pytest.mark.parametrize(
    "url",
    [
        "https://localhost/",
        "https://127.0.0.1/",
        "https://10.0.0.1/",
        "javascript:alert(1)",
        "https://user@cnops.org.ma/",
    ],
)
def test_general_web_rejects_private_or_unsafe_links(url):
    assert not health_url(url, domains=None)


def test_general_web_answer_about_a_city_is_not_replaced_by_pharmacies(
    pipeline, monkeypatch
):
    monkeypatch.setenv("ASSISTANT_WEB_FIRST", "true")
    monkeypatch.setenv("ASSISTANT_AGENT", "true")
    monkeypatch.setattr(
        "pharma_assistant.nlp.agent.run_agent",
        lambda *a, **k: {
            "answer": "Réponse météo issue des sources consultées.",
            "model": "test-model",
            "answer_source": "openrouter_agent",
            "pharmacies": [],
            "web_search": {"attempted": True, "succeeded": True},
        },
    )
    question = "Quelle météo à Rabat ?"
    result = answer_from_data(
        OpenRouterPipeline(pipeline, PROVIDER), pipeline.analyze(question), question
    )
    assert result["answer_source"] == "openrouter_agent"
    assert result["answer"].startswith("Réponse météo")


def test_cited_cnops_records_are_checked_without_relying_on_nlu():
    row = search("Panadol")[0]
    reply = AgentReply(
        answer="Le prix est 999 MAD.", source_ids=[row["id"]], kind="information"
    )
    with pytest.raises(ValueError):
        validate_cnops_claims(
            reply, {row["id"]: {**row, "kind": "cnops_record"}}, False
        )
