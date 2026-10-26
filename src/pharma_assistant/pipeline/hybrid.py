"""Use supervised routing only where baseline safety/evidence permits it."""

from pharma_assistant.api.schemas import AnalysisResponse


class HybridPipeline:
    """Retain validated reference extraction and clinical refusal from the baseline."""

    def __init__(self, baseline, learned, threshold: float = 0.7) -> None:
        self.baseline, self.learned, self.threshold = baseline, learned, threshold
        self.extractor = baseline.extractor

    def analyze(
        self, text: str, *, language_hint: str | None = None
    ) -> AnalysisResponse:
        """Fall back when learned routing conflicts with schema or clinical safety."""
        result = self.baseline.analyze(text, language_hint=language_hint)
        predicted = self.learned.predict(text)
        if (
            result.intent.label == "out_of_scope"
            or result.contains_out_of_scope_request
        ):
            return result
        if predicted["intent"]["confidence"] < self.threshold:
            return result
        payload = result.model_dump(mode="json", by_alias=True)
        payload["intent"] = predicted["intent"]
        info = {
            "pharmacy_info_phone": "phone",
            "pharmacy_info_location": "location",
            "pharmacy_info_hours": "hours",
        }.get(payload["intent"]["label"])
        payload["pharmacy_query"] = {
            "needs_pharmacy_info": bool(info),
            "info_type": info,
        }
        try:
            return AnalysisResponse.model_validate(payload)
        except ValueError:
            return result
