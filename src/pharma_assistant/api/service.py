"""Analysis/search endpoints; initialize models explicitly and return safe errors."""

import os
import tempfile
import threading
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel, ConfigDict, Field

from pharma_assistant.api.schemas import DISCLAIMER, AnalysisResponse, Language
from pharma_assistant.asr.transcriber import Transcription
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


def grounded_pipeline(request: Request) -> TextPipeline:
    """Keep consumer answers independent from optional research/LLM tracks."""
    current = getattr(request.app.state, "pipeline", None)
    if isinstance(current, TextPipeline):
        return current
    if getattr(request.app.state, "consumer_pipeline", None) is None:
        with _INIT_LOCK:
            if getattr(request.app.state, "consumer_pipeline", None) is None:
                try:
                    request.app.state.consumer_pipeline = TextPipeline.from_config()
                except (FileNotFoundError, ValueError) as error:
                    raise HTTPException(
                        503, "Reference database unavailable"
                    ) from error
    return request.app.state.consumer_pipeline


@router.get("/version")
def version() -> dict:
    """Distinguish application version from reference/model readiness."""
    return {
        "version": "0.2.0",
        "pipeline": "rule_baseline_v1",
        "consumer_policy": "grounded_v2",
        "voice_flow": "confirm_transcript",
        "jury_matching": "exact_questions_v2",
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


async def transcribe_upload(
    request: Request, file: UploadFile, language_hint: Language | None = None
) -> Transcription:
    """Decode and transcribe an upload, without interpreting unconfirmed words."""
    from starlette.concurrency import run_in_threadpool

    from pharma_assistant.asr.transcriber import WhisperTranscriber

    config = load_config(Path("configs/asr.yaml"))
    data = await file.read(config["max_bytes"] + 1)
    if not data or len(data) > config["max_bytes"]:
        raise HTTPException(413, "Audio empty or too large")
    # ffprobe/ffmpeg must reopen this path. An open NamedTemporaryFile is locked
    # against other processes on Windows, so write and close inside a directory.
    with tempfile.TemporaryDirectory(prefix="pharma_upload_") as directory:
        audio_path = Path(directory) / "upload.audio"
        audio_path.write_bytes(data)
        try:
            from pharma_assistant.asr.transcriber import validate_audio

            await run_in_threadpool(validate_audio, audio_path, config)
        except OSError as error:
            raise HTTPException(
                503, "Audio tools unavailable; install ffmpeg and ffprobe and restart"
            ) from error
        except ValueError as error:
            raise HTTPException(415, str(error)) from error
        try:
            if getattr(request.app.state, "transcriber", None) is None:
                request.app.state.transcriber = await run_in_threadpool(
                    WhisperTranscriber, config
                )
            evidence = await run_in_threadpool(
                request.app.state.transcriber.transcribe,
                audio_path,
                **(
                    {"language": "fr" if language_hint == "fr" else "ar"}
                    if language_hint in {"fr", "ar", "darija_ar", "darija_latn"}
                    else {}
                ),
            )
        except (ImportError, RuntimeError, OSError) as error:
            raise HTTPException(
                503, "ASR unavailable; install speech extras and cache local weights"
            ) from error
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
    if not evidence.text.strip() or len(evidence.text) > 10000:
        raise HTTPException(422, "No usable speech transcript")
    return evidence


@router.post("/v1/transcribe/voice")
async def transcribe_voice(
    request: Request,
    file: Annotated[UploadFile, File()],
    language_hint: Annotated[Language | None, Form()] = None,
) -> dict:
    """Return unconfirmed speech evidence, never pharmacy or stock assertions."""
    evidence = await transcribe_upload(request, file, language_hint)
    return {"transcript": evidence.text, "requires_confirmation": True}


@router.post("/v1/analyze/voice", response_model=AnalysisResponse)
async def analyze_voice(
    request: Request,
    file: Annotated[UploadFile, File()],
    language_hint: Annotated[Language | None, Form()] = None,
) -> AnalysisResponse:
    """Retain the machine-consumer voice analysis contract."""
    from starlette.concurrency import run_in_threadpool

    evidence = await transcribe_upload(request, file, language_hint)
    result = await run_in_threadpool(
        pipeline(request).analyze, evidence.text, language_hint=language_hint
    )
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


@router.get("/v1/voice/status")
def voice_status() -> dict:
    """Check local prerequisites without downloading or loading ASR model weights."""
    from pharma_assistant.asr.readiness import check_voice

    return {
        **check_voice(load_config(Path("configs/asr.yaml"))),
        "disclaimer": DISCLAIMER,
    }


@router.post("/v1/assistant/text")
def assistant_text(body: TextRequest, request: Request) -> dict:
    """Present a bounded, readable answer while keeping the analysis API stable."""
    from pharma_assistant.api.answers import present_answer

    if not body.text.strip():
        raise HTTPException(422, "Text must be nonblank")
    analysis = grounded_pipeline(request).analyze(
        body.text, language_hint=body.language_hint
    )
    payload = analysis.model_dump(mode="json", by_alias=True)
    payload["request_id"] = request.state.request_id
    return present_answer(AnalysisResponse.model_validate(payload), body.user_location)


@router.post("/v1/assistant/voice")
async def assistant_voice(
    request: Request,
    file: Annotated[UploadFile, File()],
    language_hint: Annotated[Language | None, Form()] = None,
) -> dict:
    """Use the same answer presenter for voice, with visible transcript evidence."""
    from starlette.concurrency import run_in_threadpool

    from pharma_assistant.api.answers import present_answer

    evidence = await transcribe_upload(request, file, language_hint)
    analysis = await run_in_threadpool(
        grounded_pipeline(request).analyze, evidence.text, language_hint=language_hint
    )
    payload = analysis.model_dump(mode="json", by_alias=True)
    payload["input"].update(modality="voice", raw_text="", transcript=evidence.text)
    payload["request_id"] = request.state.request_id
    return present_answer(AnalysisResponse.model_validate(payload))


@router.post("/v1/demo/assistant/text")
def demo_assistant_text(body: TextRequest) -> dict:
    """Explicit fictional scenario; never infer simulated availability in real mode."""
    from pharma_assistant.api.jury_scenario import scenario_answer

    if not body.text.strip():
        raise HTTPException(422, "Text must be nonblank")
    return scenario_answer(body.text, body.language_hint)


@router.post("/v1/demo/assistant/voice")
async def demo_assistant_voice(
    request: Request,
    file: Annotated[UploadFile, File()],
    language_hint: Annotated[Language | None, Form()] = None,
) -> dict:
    """Transcribe actual audio, then query the same visibly fictional scenario."""
    from pharma_assistant.api.jury_scenario import scenario_answer

    evidence = await transcribe_upload(request, file, language_hint)
    result = scenario_answer(evidence.text, language_hint)
    result["transcript"] = evidence.text
    return result
