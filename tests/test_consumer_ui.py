"""Consumer interface abstraction, asset access and protected API boundaries."""

from html.parser import HTMLParser
from pathlib import Path

from fastapi.testclient import TestClient

from pharma_assistant.api.app import create_app

ROOT = Path(__file__).resolve().parents[1]


class VisibleCopy(HTMLParser):
    """Collect rendered copy without conflating implementation source with UI text."""

    def __init__(self):
        super().__init__()
        self.copy = []
        self.inputs = []

    def handle_data(self, data):
        self.copy.append(data)

    def handle_starttag(self, tag, attrs):
        if tag in {"input", "textarea", "select"}:
            self.inputs.append(dict(attrs))


def test_consumer_html_has_no_technical_panels_or_credentials():
    parser = VisibleCopy()
    parser.feed((ROOT / "web/index.html").read_text(encoding="utf-8"))
    text = " ".join(parser.copy).casefold()
    for term in [
        "json",
        "api key",
        "clé api",
        "ffmpeg",
        "whisper",
        "python",
        "uv sync",
        "latitude",
        "longitude",
        "détails techniques",
    ]:
        assert term not in text
    assert all(item.get("type") != "password" for item in parser.inputs)
    assert {item["id"] for item in parser.inputs} == {
        "language",
        "audio-file",
        "message",
        "map-city",
        "map-radius",
    }


def test_assets_public_does_not_expose_protected_analysis(monkeypatch):
    monkeypatch.setenv("API_KEY", "fixture-key")
    with TestClient(create_app()) as client:
        assert client.get("/").status_code == 200
        for filename in ["assistant.css", "assistant.js", "pharmacy-robot.webp"]:
            response = client.get("/ui/" + filename)
            assert response.status_code == 200 and response.content
            if filename.endswith((".css", ".js")):
                assert "fixture-key" not in response.text
        assert (
            client.post("/v1/assistant/text", json={"text": "salam"}).status_code == 401
        )
        assert client.get("/v1/voice/status").status_code == 401
        assert client.get("/ui/not-an-asset").status_code == 404


def test_frontend_uses_consumer_reply_without_rendering_analysis():
    script = (ROOT / "web/assets/assistant.js").read_text(encoding="utf-8")
    assert "data.answer" in script
    assert "data.analysis" not in script
    assert "innerHTML" not in script
    assert "localStorage" not in script
    assert "sessionStorage" not in script
