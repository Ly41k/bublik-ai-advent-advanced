"""Explicit request and response models."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints

from bublik.domain.task import TaskStatus

TaskTitle = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200, strict=True)
]


class HealthResponse(BaseModel):
    """Service liveness response."""

    status: Literal["ok"] = "ok"


class CreateTaskRequest(BaseModel):
    """Only the title is writable when creating a task."""

    model_config = ConfigDict(extra="forbid")

    title: TaskTitle


class UpdateTaskStatusRequest(BaseModel):
    """Only a supported status is writable through the status endpoint."""

    model_config = ConfigDict(extra="forbid")

    status: TaskStatus


class TaskResponse(BaseModel):
    """Public task representation mapped from a domain value."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    status: TaskStatus
