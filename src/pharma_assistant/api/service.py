"""Analysis/search endpoints; initialize models explicitly and return safe errors."""

import os
import tempfile
import threading
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel, ConfigDict, Field

from pharma_assistant.api.schemas import DISCLAIMER, AnalysisResponse, Language
from pharma_assistant.data.pharmacies import PharmacyRepository
from pharma_assistant.data_tools.fetch_pharmacies import load_config
from pharma_assistant.pipeline.text_pipeline import TextPipeline

router = APIRouter()
_INIT_LOCK = threading.Lock()


class Location(BaseModel):
    """Validated geographic hint; never infer an address from IP."""

    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)


class TextRequest(BaseModel):
    """Bounded text and optional language/location hints."""

    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=10000)
    language_hint: Language | None = None
    user_location: Location | None = None


def pipeline(request: Request):
    """Load once on first use; absent reference data yields a clear 503."""
    if getattr(request.app.state, "pipeline", None) is None:
        with _INIT_LOCK:
            if getattr(request.app.state, "pipeline", None) is None:
                try:
                    baseline = TextPipeline.from_config()
                    track = os.getenv("NLU_TRACK", "baseline")
                    if track == "hybrid":
                        import pickle

                        from pharma_assistant.pipeline.hybrid import HybridPipeline

                        model = pickle.loads(
                            Path(
                                os.getenv("NLU_MODEL_PATH", "models/char_wb/model.pkl")
                            ).read_bytes()
                        )
                        request.app.state.pipeline = HybridPipeline(baseline, model)
                    elif track == "llm":
                        from pharma_assistant.nlp.llm import (
                            HTTPJSONProvider,
                            LLMExtractor,
                        )

                        endpoint = os.getenv("LLM_ENDPOINT", "")
                        key = os.getenv("LLM_API_KEY", "")
                        if not endpoint or not key:
                            raise ValueError("LLM endpoint/key absent")
                        request.app.state.pipeline = LLMExtractor(
                            HTTPJSONProvider(endpoint, key), baseline
                        )
                    elif track == "baseline":
                        request.app.state.pipeline = baseline
                    else:
                        raise ValueError("Unknown NLU_TRACK")
                except (FileNotFoundError, ValueError) as error:
                    raise HTTPException(
                        503, "Reference database unavailable; run make medications"
                    ) from error
    return request.app.state.pipeline


@router.get("/version")
def version() -> dict:
    """Distinguish application version from reference/model readiness."""
    return {
        "version": "0.2.0",
        "pipeline": "rule_baseline_v1",
        "medical_advice": False,
        "disclaimer": DISCLAIMER,
    }


@router.post("/v1/analyze/text", response_model=AnalysisResponse)
def analyze_text(body: TextRequest, request: Request) -> AnalysisResponse:
    """Return structured evidence, never a stock claim or medical recommendation."""
    if not body.text.strip():
        raise HTTPException(422, "Text must be nonblank")
    result = pipeline(request).analyze(body.text, language_hint=body.language_hint)
    payload = result.model_dump(mode="json", by_alias=True)
    payload["request_id"] = request.state.request_id
    return AnalysisResponse.model_validate(payload)


@router.post("/v1/analyze/voice", response_model=AnalysisResponse)
async def analyze_voice(
    request: Request, file: Annotated[UploadFile, File()]
) -> AnalysisResponse:
    """Bound uploads and decode audio before optional local-model inference."""
    from starlette.concurrency import run_in_threadpool

    from pharma_assistant.asr.transcriber import WhisperTranscriber

    config = load_config(Path("configs/asr.yaml"))
    data = await file.read(config["max_bytes"] + 1)
    if not data or len(data) > config["max_bytes"]:
        raise HTTPException(413, "Audio empty or too large")
    with tempfile.NamedTemporaryFile(suffix=".audio") as handle:
        handle.write(data)
        handle.flush()
        try:
            from pharma_assistant.asr.transcriber import validate_audio

            await run_in_threadpool(validate_audio, Path(handle.name), config)
        except ValueError as error:
            raise HTTPException(415, str(error)) from error
        try:
            if getattr(request.app.state, "transcriber", None) is None:
                request.app.state.transcriber = await run_in_threadpool(
                    WhisperTranscriber, config
                )
            evidence = await run_in_threadpool(
                request.app.state.transcriber.transcribe, Path(handle.name)
            )
        except (ImportError, RuntimeError, OSError) as error:
            raise HTTPException(
                503, "ASR unavailable; install speech extras and cache local weights"
            ) from error
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
    result = await run_in_threadpool(pipeline(request).analyze, evidence.text)
    payload = result.model_dump(mode="json", by_alias=True)
    payload["input"].update(modality="voice", raw_text="", transcript=evidence.text)
    payload["request_id"] = request.state.request_id
    return AnalysisResponse.model_validate(payload)


@router.get("/v1/medications/search")
def medication_search(
    request: Request, q: str = Query(default="", max_length=500), k: int = 3
) -> dict:
    """Return source-backed candidates and uncertainty, never a substitution choice."""
    if not q.strip() or not 1 <= k <= 10:
        raise HTTPException(422, "Nonblank q and k in [1,10] required")
    results = pipeline(request).extractor.index.search(q, k=k)
    return {
        "candidates": [candidate.model_dump(mode="json") for candidate in results],
        "disclaimer": "Cet assistant ne fournit pas de conseil médical.",
    }


@router.get("/v1/pharmacies/nearby")
def pharmacies_nearby(lat: float, lon: float, k: int = 5) -> dict:
    """Return actual static directory records, with missing hours/phones preserved."""
    try:
        Location(latitude=lat, longitude=lon)
        if not 1 <= k <= 20:
            raise ValueError("k must be in [1,20]")
        repository = PharmacyRepository(Path("data/pharmacies/pharmacies.sqlite3"))
        results = repository.nearest(lat, lon, k)
    except FileNotFoundError as error:
        raise HTTPException(
            503, "Directory unavailable; run make pharmacies"
        ) from error
    except ValueError as error:
        raise HTTPException(422, "Invalid coordinates or k") from error
    return {
        "pharmacies": [row.model_dump(mode="json") for row in results],
        "live_duty_status": False,
        "disclaimer": "Cet assistant ne fournit pas de conseil médical.",
    }


@router.get("/v1/pharmacies/map")
def pharmacies_map(
    lat: float = Query(ge=-90, le=90, allow_inf_nan=False),
    lon: float = Query(ge=-180, le=180, allow_inf_nan=False),
    radius_km: float = Query(default=5, gt=0, le=100, allow_inf_nan=False),
) -> dict:
    """Return all saved records inside a radius and a Plotly Express figure."""
    from pharma_assistant.api.pharmacy_map import make_map

    try:
        rows = PharmacyRepository(
            Path("data/pharmacies/pharmacies.sqlite3")
        ).within_radius(lat, lon, radius_km)
    except FileNotFoundError as error:
        raise HTTPException(
            503, "Directory unavailable; run make pharmacies"
        ) from error
    return {
        "pharmacies": [row.model_dump(mode="json") for row in rows],
        "count": len(rows),
        "radius_km": radius_km,
        "figure": make_map(rows, lat, lon, radius_km),
        "coverage": "Saved OpenStreetMap snapshot; coverage may be incomplete.",
        "attribution": "© OpenStreetMap contributors · ODbL 1.0",
        "live_duty_status": False,
        "disclaimer": DISCLAIMER,
    }
