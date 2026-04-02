"""Pydantic-модели для задач, статусов агентов и запросов на одобрение."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TaskStatus(str, Enum):
    """Статус задачи."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"


class Task(BaseModel):
    """Задача для агента."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str
    created_by: str
    assigned_to: str
    status: TaskStatus = TaskStatus.PENDING
    priority: int = Field(ge=1, le=5, default=3)
    payload: dict = Field(default_factory=dict)
    result: dict | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    completed_at: datetime | None = None
    requires_approval: bool = False


class AgentStatus(BaseModel):
    """Статус агента в системе."""

    agent_id: str
    status: str = "offline"  # online, offline, busy, error
    last_heartbeat: datetime = Field(default_factory=_utcnow)
    current_task_id: str | None = None
    model: str | None = None
    version: str = "0.1.0"


class ApprovalRequest(BaseModel):
    """Запрос на одобрение критичной операции."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    task_id: str
    agent_id: str
    action: str  # "change_price", "create_supply", etc.
    description: str  # Описание для человека
    details: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utcnow)
    timeout_minutes: int = 30


class ApprovalResult(BaseModel):
    """Результат одобрения от человека."""

    request_id: str
    approved: bool
    decided_by: str  # Telegram user info
    decided_at: datetime = Field(default_factory=_utcnow)
    comment: str | None = None


class ToolCallRequest(BaseModel):
    """Запрос на вызов инструмента MCP."""

    tool: str
    params: dict = Field(default_factory=dict)


class ToolCallResponse(BaseModel):
    """Ответ от MCP-сервера на вызов инструмента."""

    success: bool
    data: dict | list | None = None
    error: str | None = None
