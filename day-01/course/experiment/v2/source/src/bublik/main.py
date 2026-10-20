"""Application factory and the sole composition root."""

from fastapi import FastAPI

from bublik.api.routes import router
from bublik.application.service import TaskService
from bublik.infrastructure.memory_repository import InMemoryTaskRepository


def create_app() -> FastAPI:
    """Create an application with its own repository and service."""
    app = FastAPI(title="Bublik Task Service", version="0.1.0")
    app.state.task_service = TaskService(InMemoryTaskRepository())
    app.include_router(router)
    return app
