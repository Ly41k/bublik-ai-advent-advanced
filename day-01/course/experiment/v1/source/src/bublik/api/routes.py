"""Thin HTTP handlers delegating task use cases to the service."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from bublik.api.dependencies import get_task_service
from bublik.api.schemas import (
    CreateTaskRequest,
    HealthResponse,
    TaskResponse,
    UpdateTaskStatusRequest,
)
from bublik.application.service import TaskService
from bublik.domain.errors import TaskNotFoundError

router = APIRouter()
TaskServiceDependency = Annotated[TaskService, Depends(get_task_service)]


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Report that the application can handle requests."""
    return HealthResponse()


@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: CreateTaskRequest, service: TaskServiceDependency) -> TaskResponse:
    """Create a task through the application service."""
    task = service.create_task(payload.title)
    return TaskResponse.model_validate(task)


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: UUID, service: TaskServiceDependency) -> TaskResponse:
    """Map an absent task to the documented HTTP error."""
    try:
        task = service.get_task(task_id)
    except TaskNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return TaskResponse.model_validate(task)


@router.patch("/tasks/{task_id}/status", response_model=TaskResponse)
def update_task_status(
    task_id: UUID, payload: UpdateTaskStatusRequest, service: TaskServiceDependency
) -> TaskResponse:
    """Update a task's status and map an absent task to HTTP 404."""
    try:
        task = service.update_task_status(task_id, payload.status)
    except TaskNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return TaskResponse.model_validate(task)
