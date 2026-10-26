"""Resolve the service owned by the current application instance."""

from fastapi import Request

from bublik.application.service import TaskService


def get_task_service(request: Request) -> TaskService:
    """Return the service wired by the application factory."""
    service = request.app.state.task_service
    if not isinstance(service, TaskService):
        raise TypeError("Application task service is not configured")
    return service
