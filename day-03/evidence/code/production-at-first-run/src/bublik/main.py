"""Application factory and the sole composition root."""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pathlib import Path

from bublik.api.routes import router
from bublik.application.service import TaskService
from bublik.infrastructure.memory_repository import InMemoryTaskRepository


def create_app() -> FastAPI:
    """Create an application with its own repository and service."""
    app = FastAPI(title="Bublik Task Service", version="0.1.0")
    app.state.task_service = TaskService(InMemoryTaskRepository())
    app.include_router(router)

    @app.get("/ui", response_class=HTMLResponse, include_in_schema=False)
    def task_ui() -> str:
        """Serve the single Day 3 task page."""
        return Path(__file__).with_name("ui.html").read_text(encoding="utf-8")

    return app
