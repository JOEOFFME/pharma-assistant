"""FastAPI application factory and ASGI entry point."""

from fastapi import FastAPI

from pharma_assistant import __version__
from pharma_assistant.api.health import router


def create_app() -> FastAPI:
    """Build an isolated application with no downloads or database side effects."""
    application = FastAPI(
        title="Pharma Assistant",
        version=__version__,
        description=(
            "Arabic/Darija/French patient-pharmacy assistance prototype. "
            "Cet assistant ne fournit pas de conseil médical. "
            "TASK 0: health endpoint only."
        ),
    )
    application.include_router(router)
    return application


app = create_app()
