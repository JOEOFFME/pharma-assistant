"""Provider-neutral strict-JSON extraction with bounded retries and safe fallback."""

import json
import re
from typing import Protocol
from urllib.request import Request, urlopen

from pharma_assistant.api.schemas import AnalysisResponse


class JSONProvider(Protocol):
    """A provider accepts text/schema and returns a JSON string, without free advice."""

    def extract(self, text: str, schema: dict, timeout: float) -> str:
        """Produce a candidate response for schema validation."""
        ...


class HTTPJSONProvider:
    """Adapter contract: POST {text,schema}, return a complete v1 response JSON."""

    def __init__(self, url: str, api_key: str) -> None:
        if not url.startswith("https://"):
            raise ValueError("Provider endpoint must use HTTPS")
        self.url, self.api_key = url, api_key

    def extract(self, text: str, schema: dict, timeout: float) -> str:
        """Keep credentials out of URLs/logs and bound response size/time."""
        request = Request(
            self.url,
            data=json.dumps({"text": text, "schema": schema}).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + self.api_key,
            },
            method="POST",
        )
        with urlopen(request, timeout=timeout) as response:
            data = response.read(131073)
        if len(data) > 131072:
            raise ValueError("Provider response too large")
        return data.decode("utf-8")


class FakeLLM:
    """Test fixture only; never report this as an actual LLM benchmark."""

    def __init__(self, responses: list[str]) -> None:
        self.responses = iter(responses)

    def extract(self, text: str, schema: dict, timeout: float) -> str:
        """Return a supplied fixture, including invalid-response cases."""
        return next(self.responses)


class LLMExtractor:
    """Reject schema/evidence violations and fall back to the baseline on failure."""

    def __init__(
        self, provider: JSONProvider, baseline, attempts: int = 2, timeout: float = 10
    ) -> None:
        if not 1 <= attempts <= 3 or not 0 < timeout <= 60:
            raise ValueError("Invalid provider retry/timeout bounds")
        self.extractor = baseline.extractor
        self.provider, self.baseline, self.attempts, self.timeout = (
            provider,
            baseline,
            attempts,
            timeout,
        )

    def analyze(
        self, text: str, *, language_hint: str | None = None
    ) -> AnalysisResponse:
        """The rule safety router remains authoritative for clinical requests."""
        safe = self.baseline.analyze(text, language_hint=language_hint)
        for _ in range(self.attempts):
            try:
                result = AnalysisResponse.model_validate_json(
                    self.provider.extract(
                        text, AnalysisResponse.model_json_schema(), self.timeout
                    )
                )
                if result.input.raw_text != text or result.input.modality != "text":
                    raise ValueError("Provider rewrote the input")
                if (
                    safe.intent.label == "out_of_scope"
                    or safe.contains_out_of_scope_request
                ):
                    return safe
                payload = result.model_dump(mode="json", by_alias=True)
                # Provider-supplied identities are claims; ground them in the reference.
                for entity in payload["entities"]:
                    if entity["start"] is None or entity["end"] is None:
                        raise ValueError(
                            "LLM output requires explicit evidence offsets"
                        )
                    if entity["type"] != "MEDICATION":
                        continue
                    entity.update(normalized=None, matched_id=None, dci=None)
                    candidates = self.baseline.extractor.index.search(
                        entity["text"], k=3
                    )
                    if (
                        candidates
                        and candidates[0].score >= 0.9
                        and not candidates[0].needs_clarification
                    ):
                        record = candidates[0].medication
                        entity.update(
                            normalized=record.brand_name,
                            matched_id=record.id,
                            dci=record.dci,
                        )
                    else:
                        payload["needs_clarification"] = True
                        payload["clarification_question"] = {
                            "fr": "Pouvez-vous préciser le produit ?"
                        }
                # Only fixed safe templates may become clarification responses.
                payload["clarification_question"] = {
                    "fr": (
                        "Pouvez-vous préciser le produit ou la demande ?"
                        if payload["needs_clarification"]
                        else None
                    ),
                    "ar": None,
                }
                for entity in payload["entities"]:
                    if entity["type"] in {"LOCATION", "PHARMACY_NAME", "FORM"}:
                        entity["normalized"] = None
                    if entity["type"] == "QUANTITY":
                        quantity = re.match(r"[1-9]\d*", entity["text"])
                        if quantity:
                            package = (
                                entity["text"][quantity.end() :].strip().casefold()
                            )
                            expected_unit = (
                                self.baseline.config["quantity_units"].get(package)
                                if package
                                else "unit"
                            )
                            if (
                                int(quantity.group()) != entity["value"]
                                or expected_unit != entity["unit"]
                            ):
                                raise ValueError("Provider quantity contradicts source")
                        elif entity["text"] in {"علبتين", "علبتان"}:
                            if entity["value"] != 2 or entity["unit"] != "box":
                                raise ValueError(
                                    "Provider dual count contradicts source"
                                )
                        else:
                            raise ValueError(
                                "Quantity needs deterministic source parsing"
                            )
                    if entity["type"] == "DOSAGE" and entity["value"] is not None:
                        scalar = re.fullmatch(
                            r"(\d+(?:[.,]\d+)?)\s*(mg/mL|g/L|mcg|mg|g|IU|%|غ|ملغ)",
                            entity["text"],
                            re.I,
                        )
                        if (
                            not scalar
                            or float(scalar[1].replace(",", ".")) != entity["value"]
                        ):
                            raise ValueError("Provider strength contradicts source")
                        unit = {
                            "غ": "g",
                            "ملغ": "mg",
                            "iu": "IU",
                            "mg/ml": "mg/mL",
                            "g/l": "g/L",
                        }.get(scalar[2].lower(), scalar[2].lower())
                        if unit != entity["unit"]:
                            raise ValueError(
                                "Provider strength unit contradicts source"
                            )
                if language_hint is not None:
                    payload["input"]["language"] = language_hint
                return AnalysisResponse.model_validate(payload)
            except (ValueError, OSError, StopIteration):
                continue
        return safe
