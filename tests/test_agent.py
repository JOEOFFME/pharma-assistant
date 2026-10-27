"""Tool-agent behavior with mocked paid transport and real local catalogue data."""

import io
import json

import pytest
from fastapi.testclient import TestClient

from pharma_assistant.api.app import create_app
from pharma_assistant.nlp.agent import PharmacyTools, health_url, run_agent
from pharma_assistant.nlp.mcp_stdio import serve
from pharma_assistant.nlp.openrouter import OpenRouterProvider

PROVIDER = OpenRouterProvider("test-only-secret", "openai/gpt-4.1")
URL = "https://www.nhs.uk/conditions/migraine/treatment/"


def final(
    answer=(
        "Ma kaynch dwa wa7ed. Les triptans men traitements dyal migraine. "
        "Hadi ma3louma 3amma, machi ikhtiyar dwa lik."
    ),
    ids=None,
    kind="information",
):
    return {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": json.dumps(
                        {
                            "answer": answer,
                            "source_ids": ["web:1"] if ids is None else ids,
                            "kind": kind,
                        }
                    )
                },
            }
        ],
        "model": "openai/gpt-4.1",
    }


def call(name="search_health_web", query="migraine general treatment names"):
    return {
        "choices": [
            {
                "finish_reason": "tool_calls",
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
                },
            }
        ]
    }


def research(url=URL):
    return {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": (
                        "General migraine treatments include triptans. "
                        "Individual suitability needs assessment."
                    ),
                    "annotations": [
                        {
                            "type": "url_citation",
                            "url_citation": {
                                "url": url,
                                "title": "Migraine treatment — NHS",
                                "content": "Triptans treat migraine.",
                            },
                        }
                    ],
                },
            }
        ]
    }


@pytest.mark.parametrize(
    "question,history",
    [
        ("chnu smiya dyal dwa dyal la migraine ?", []),
        ("Dwa dyal la Migraine", []),
        ("bghit ghir smya dyalo", [{"role": "user", "text": "Dwa dyal la Migraine"}]),
    ],
)
def test_migraine_and_followup_use_research_not_blanket_refusal(
    pipeline, monkeypatch, question, history
):
    responses = iter([call(), research(), final()])
    bodies = []

    def transport(provider, body, timeout):
        bodies.append(body)
        return next(responses)

    monkeypatch.setattr("pharma_assistant.nlp.agent.chat", transport)
    result = run_agent(PROVIDER, pipeline, question, "darija_latn", history=history)
    assert result["answer_source"] == "openrouter_agent"
    assert "triptans" in result["answer"]
    assert result["sources"][0]["url"] == URL
    assert result["tools_used"] == ["search_health_web"]
    assert bodies[1]["plugins"][0]["id"] == "web"
    assert bodies[1]["plugins"][0]["engine"] == "exa"
    assert "test-only-secret" not in json.dumps(bodies)
    assert any(m.get("content") == question for m in bodies[0]["messages"])
    if history:
        assert any(m["content"] == history[0]["text"] for m in bodies[0]["messages"])


def test_consumer_route_does_not_run_refusal_planner_before_agent(
    pipeline, monkeypatch
):
    monkeypatch.setenv("ASSISTANT_AGENT", "true")
    monkeypatch.setenv("ASSISTANT_NLU", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-only-secret")
    monkeypatch.setattr(
        OpenRouterProvider,
        "plan",
        lambda *a, **k: pytest.fail("Extra NLU planner must not block agent"),
    )
    responses = iter([call(), research(), final()])
    monkeypatch.setattr(
        "pharma_assistant.nlp.agent.chat", lambda *a, **k: next(responses)
    )
    app = create_app()
    app.state.pipeline = pipeline
    with TestClient(app) as client:
        response = client.post(
            "/v1/assistant/text",
            json={"text": "Dwa dyal la Migraine", "language_hint": "darija_latn"},
        )
    assert response.status_code == 200
    assert response.json()["answer_source"] == "openrouter_agent"
    assert "triptans" in response.json()["answer"]


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "https://nhs.uk.evil.test/path",
        "http://www.nhs.uk/path",
        "https://user@nhs.uk/path",
        "https://127.0.0.1/path",
        "https://nhs.uk:invalid/path",
    ],
)
def test_untrusted_citation_urls_are_rejected(url):
    assert not health_url(url)


def test_web_failure_is_visible_to_agent_not_faked_as_success(pipeline, monkeypatch):
    responses = iter(
        [
            call(),
            research("https://evil.test"),
            final(
                "Ma 9dertch nverifi had lma3louma daba.", ids=[], kind="clarification"
            ),
        ]
    )
    bodies = []

    def transport(*args, **kwargs):
        bodies.append(args[1])
        return next(responses)

    monkeypatch.setattr("pharma_assistant.nlp.agent.chat", transport)
    result = run_agent(PROVIDER, pipeline, "migraine ?", "darija_latn")
    assert result["sources"] == []
    assert result["tools_used"] == []
    assert "Tool unavailable" in bodies[-1]["messages"][-1]["content"]


@pytest.mark.parametrize(
    "reply",
    [
        final(ids=["invented"]),
        final(ids=[]),
        final("Prenez 500 mg deux fois par jour.", ids=[], kind="medical_boundary"),
    ],
)
def test_invalid_or_dosing_answer_rejected(pipeline, monkeypatch, reply):
    monkeypatch.setattr("pharma_assistant.nlp.agent.chat", lambda *a, **k: reply)
    with pytest.raises(ValueError):
        run_agent(PROVIDER, pipeline, "migraine ?", "fr")


def test_tools_are_bounded_validated_and_have_actual_provenance(pipeline, monkeypatch):
    tools = PharmacyTools(pipeline, PROVIDER)
    medication = tools.call("search_medications", {"query": "Doliprane"})
    assert medication["medications"]
    assert medication["medications"][0]["source_country"] == "FR"
    directory = tools.call("search_pharmacies", {"query": "Pharmacies à Rabat"})
    assert directory["pharmacies"]
    assert all(p["city"] == "Rabat" for p in directory["pharmacies"])
    assert directory["current_duty"] == "unverified"
    with pytest.raises(ValueError):
        tools.call("execute_shell", {"query": "anything"})
    with pytest.raises(ValueError):
        tools.call(
            "search_medications", {"query": "Doliprane", "url": "http://localhost"}
        )
    monkeypatch.setenv("ASSISTANT_WEB_SEARCH", "false")
    assert "search_health_web" not in {d["name"] for d in tools.definitions()}


def test_tool_rounds_cannot_loop_forever(pipeline, monkeypatch):
    calls = []

    def repeated(*a, **k):
        calls.append(a[1])
        return call("search_medications", "Doliprane")

    monkeypatch.setattr("pharma_assistant.nlp.agent.chat", repeated)
    with pytest.raises(ValueError):
        run_agent(PROVIDER, pipeline, "Doliprane", "fr")
    assert len(calls) == 4
    assert calls[-1]["tool_choice"] == "none"


def test_mcp_initialize_discover_execute_and_error_protocol(pipeline):
    requests = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-06-18"},
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "search_medications",
                "arguments": {"query": "Doliprane"},
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "search_medications",
                "arguments": {"query": "x", "unexpected": "value"},
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {"name": "shell"},
        },
    ]
    output = io.StringIO()
    serve(
        PharmacyTools(pipeline),
        io.StringIO("\n".join(json.dumps(x) for x in requests)),
        output,
    )
    replies = [json.loads(line) for line in output.getvalue().splitlines()]
    assert len(replies) == 5
    assert replies[0]["result"]["capabilities"] == {"tools": {}}
    assert len(replies[1]["result"]["tools"]) == 2
    assert replies[2]["result"]["structuredContent"]["medications"]
    assert replies[3]["result"]["isError"] is True
    assert replies[4]["error"]["code"] == -32602


@pytest.mark.parametrize(
    "answer",
    [
        "Panadol est disponible à Rabat.",
        "La pharmacie est de garde ce soir.",
        "This pharmacy is open now.",
    ],
)
def test_live_claims_rejected_even_if_model_labels_as_clarification(
    pipeline, monkeypatch, answer
):
    monkeypatch.setattr(
        "pharma_assistant.nlp.agent.chat",
        lambda *a, **k: final(answer, ids=[], kind="clarification"),
    )
    with pytest.raises(ValueError):
        run_agent(PROVIDER, pipeline, "Panadol ?", "fr")


def test_research_cannot_run_twice_or_use_disabled_web(pipeline, monkeypatch):
    monkeypatch.setattr("pharma_assistant.nlp.agent.chat", lambda *a, **k: research())
    registry = PharmacyTools(pipeline, PROVIDER)
    assert registry.call("search_health_web", {"query": "migraine treatments"})[
        "sources"
    ]
    with pytest.raises(ValueError):
        registry.call("search_health_web", {"query": "migraine again"})
    monkeypatch.setenv("ASSISTANT_WEB_SEARCH", "false")
    with pytest.raises(ValueError):
        registry.call("search_health_web", {"query": "migraine"})


def test_real_transport_uses_fixed_endpoint_private_bearer_and_fallback(monkeypatch):
    from pharma_assistant.nlp.agent import chat

    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return None

        def read(self, size):
            captured["size"] = size
            return json.dumps(final(ids=[], kind="clarification")).encode()

    def transport(request, timeout):
        captured.update(
            url=request.full_url,
            headers=dict(request.header_items()),
            body=json.loads(request.data),
            timeout=timeout,
        )
        return Response()

    monkeypatch.setattr("pharma_assistant.nlp.agent.urlopen", transport)
    provider = OpenRouterProvider(
        "private-test-key", "openai/gpt-4.1", "anthropic/claude-sonnet-4.6"
    )
    chat(provider, {"messages": [{"role": "user", "content": "salam"}]}, timeout=5)
    assert captured["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer private-test-key"
    assert captured["body"]["models"] == [
        "openai/gpt-4.1",
        "anthropic/claude-sonnet-4.6",
    ]
    assert "private-test-key" not in json.dumps(captured["body"])
    assert captured["size"] == 262145


def test_sourced_general_existence_is_not_a_live_stock_claim(pipeline, monkeypatch):
    responses = iter(
        [
            call(),
            research(),
            final(
                "Kayn aktar men naw3 dyal traitement dyal migraine. "
                "Les triptans exemple 3am, machi choix dyal dwa lik."
            ),
        ]
    )
    monkeypatch.setattr(
        "pharma_assistant.nlp.agent.chat", lambda *a, **k: next(responses)
    )
    assert (
        "triptans"
        in run_agent(PROVIDER, pipeline, "migraine ?", "darija_latn")["answer"]
    )


@pytest.mark.parametrize(
    "answer",
    [
        "Panadol est disponible à Rabat.",
        "Panadol est en stock.",
        "La pharmacie est de garde.",
    ],
)
def test_web_citation_does_not_authorize_live_pharmacy_claim(
    pipeline, monkeypatch, answer
):
    responses = iter([call(), research(), final(answer)])
    monkeypatch.setattr(
        "pharma_assistant.nlp.agent.chat", lambda *a, **k: next(responses)
    )
    with pytest.raises(ValueError):
        run_agent(PROVIDER, pipeline, "migraine ?", "darija_latn")
