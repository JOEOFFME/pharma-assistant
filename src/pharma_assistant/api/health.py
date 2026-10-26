"""Liveness endpoint; intentionally independent of future data/model services."""

from typing import Literal

from fastapi import APIRouter, Response
from pydantic import BaseModel, ConfigDict

router = APIRouter(tags=["health"])
DISCLAIMER = "Cet assistant ne fournit pas de conseil medical."


class HealthResponse(BaseModel):
    """Exact health response required by TASK 0."""

    model_config = ConfigDict(extra="forbid")
    status: Literal["ok"] = "ok"


@router.get("/health", response_model=HealthResponse)
def health(response: Response) -> HealthResponse:
    """Confirm that the HTTP process is alive, without claiming model readiness."""
    response.headers["X-Medical-Disclaimer"] = DISCLAIMER
    return HealthResponse()
