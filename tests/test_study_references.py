"""Offline citation-integrity checks, not factual or external-link validation."""

import re
from pathlib import Path
from urllib.parse import urlparse

STUDY = Path(__file__).resolve().parents[1] / "docs" / "01_problem_study.md"


def test_study_citations_resolve_without_duplicate_definitions() -> None:
    """Fail on orphaned citation IDs or silently overridden reference definitions."""
    text = STUDY.read_text(encoding="utf-8")
    definitions = re.findall(r"^\[(R\d+[a-z]?)\]:\s+(\S+)$", text, re.MULTILINE)
    keys = [key for key, _ in definitions]
    used = set(re.findall(r"\[(R\d+[a-z]?)\](?!:)", text))
    assert used, "The study must cite its sources"
    assert len(keys) == len(set(keys)), "Duplicate reference definition"
    assert used == set(keys), "Unresolved or unused reference ID"
    for _, url in definitions:
        parsed = urlparse(url)
        assert parsed.scheme == "https" and parsed.hostname
        assert not parsed.username and not parsed.password


def test_related_work_entries_have_traceable_sources() -> None:
    """Every related-work entry must point to its own defined source."""
    text = STUDY.read_text(encoding="utf-8")
    entries = re.findall(
        r"^### (R\d+) - [^\n]+\n(.*?)(?=^### |^## |\Z)", text, re.M | re.S
    )
    assert len(entries) >= 8
    for identifier, body in entries:
        assert f"[{identifier}]" in body, f"Missing source in {identifier}"
        assert re.search(rf"^\[{identifier}\]: https://", text, re.MULTILINE)
