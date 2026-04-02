"""Менеджер задач — высокоуровневые операции над задачами."""

from __future__ import annotations

from datetime import datetime, timezone

import structlog

from shared.message_bus import MessageBus
from shared.models import Task, TaskStatus

logger = structlog.get_logger()


class TaskManager:
    """Управление жизненным циклом задач."""

    def __init__(self, message_bus: MessageBus) -> None:
        self._bus = message_bus

    async def create_and_assign(
        self,
        task_type: str,
        assigned_to: str,
        payload: dict | None = None,
        created_by: str = "system",
        priority: int = 3,
        requires_approval: bool = False,
    ) -> Task:
        """Создать задачу и отправить в очередь агента."""
        task = Task(
            type=task_type,
            created_by=created_by,
            assigned_to=assigned_to,
            payload=payload or {},
            priority=priority,
            requires_approval=requires_approval,
        )
        await self._bus.push_task(assigned_to, task)
        logger.info(
            "task_created",
            task_id=task.id,
            task_type=task_type,
            assigned_to=assigned_to,
        )
        return task

    async def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: dict | None = None,
        error: str | None = None,
    ) -> Task | None:
        """Обновить статус задачи."""
        task = await self._bus.get_task(task_id)
        if task is None:
            logger.warning("task_not_found", task_id=task_id)
            return None

        task.status = status
        if result is not None:
            task.result = result
        if error is not None:
            task.error = error
        if status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            task.completed_at = datetime.now(timezone.utc)

        await self._bus.store_task(task)
        logger.info("task_status_updated", task_id=task_id, status=status.value)
        return task

    async def get_recent_tasks(self, limit: int = 50) -> list[Task]:
        """Получить последние задачи."""
        return await self._bus.get_recent_tasks(limit)
