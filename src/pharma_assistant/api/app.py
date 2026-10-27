"""Bounded API service and minimal demo, without startup network/model downloads."""

import json
import logging
import os
import secrets
import threading
import time
from collections import defaultdict
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles

from pharma_assistant import __version__
from pharma_assistant.api.health import router as health_router
from pharma_assistant.api.schemas import DISCLAIMER
from pharma_assistant.api.service import router as service_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create isolated state, bounded requests and safe structured error responses."""
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
    logger.propagate = False
    application = FastAPI(
        title="Pharma-AI", version=__version__, description=DISCLAIMER
    )
    application.include_router(health_router)
    application.include_router(service_router)
    origins = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "").split(",")
        if origin.strip()
    ]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-API-Key"],
    )
    counters = defaultdict(lambda: [0, 0.0])
    lock = threading.Lock()

    def error(status: int, message: str, request_id: str) -> JSONResponse:
        return JSONResponse(
            status_code=status,
            headers={"X-Request-ID": request_id},
            content={
                "error": {"code": str(status), "message": message},
                "request_id": request_id,
                "disclaimer": DISCLAIMER,
            },
        )

    @application.middleware("http")
    async def boundaries(request: Request, call_next):
        request_id = str(uuid4())
        request.state.request_id = request_id
        started = time.perf_counter()
        public = request.url.path in {
            "/health",
            "/version",
            "/",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/assets/plotly.min.js",
        }
        public = public or request.url.path.startswith("/ui/")
        public = public or request.method == "OPTIONS"
        key = os.getenv("API_KEY", "")
        if (
            key
            and not public
            and not secrets.compare_digest(request.headers.get("x-api-key", ""), key)
        ):
            return error(401, "Invalid API key", request_id)
        if not public:
            client = request.client.host if request.client else "unknown"
            with lock:
                now = time.monotonic()
                for old in list(counters):
                    if now - counters[old][1] >= 60:
                        del counters[old]
                count, begin = counters[client]
                if count == 0:
                    begin = now
                if count >= int(os.getenv("RATE_LIMIT_PER_MINUTE", "120")):
                    return error(429, "Request limit reached", request_id)
                counters[client] = [count + 1, begin]
        if request.method == "POST":
            data = bytearray()
            async for chunk in request.stream():
                if len(data) + len(chunk) > 11 * 1024 * 1024:
                    return error(413, "Request body too large", request_id)
                data.extend(chunk)
            request._body = bytes(data)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            json.dumps(
                {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                }
            )
        )
        return response

    @application.exception_handler(HTTPException)
    async def http_error(request: Request, exception: HTTPException):
        return error(
            exception.status_code,
            str(exception.detail),
            getattr(request.state, "request_id", str(uuid4())),
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exception: RequestValidationError):
        return error(
            422,
            "Invalid request fields",
            getattr(request.state, "request_id", str(uuid4())),
        )

    @application.exception_handler(Exception)
    async def unexpected_error(request: Request, exception: Exception):
        request_id = getattr(request.state, "request_id", str(uuid4()))
        logger.error(
            json.dumps(
                {"request_id": request_id, "error_type": type(exception).__name__}
            )
        )
        return error(500, "Internal service error", request_id)

    @application.get("/", include_in_schema=False)
    def demo():
        return FileResponse(
            Path(__file__).resolve().parents[3] / "web" / "index.html",
            headers={"Cache-Control": "no-store"},
        )

    @application.get("/assets/plotly.min.js", include_in_schema=False)
    def plotly_script():
        """Serve the pinned Plotly bundle locally, without a CDN dependency."""
        import plotly

        return FileResponse(
            Path(plotly.__file__).parent / "package_data" / "plotly.min.js",
            media_type="application/javascript",
            headers={"Cache-Control": "public, max-age=3600"},
        )

    application.mount(
        "/ui",
        StaticFiles(directory=Path(__file__).resolve().parents[3] / "web" / "assets"),
        name="assistant-ui",
    )

    return application


app = create_app()
