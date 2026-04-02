"""Human-in-the-loop: запрос и обработка одобрений через Telegram."""

from __future__ import annotations

import asyncio

import structlog

from shared.message_bus import MessageBus
from shared.models import ApprovalRequest, ApprovalResult

logger = structlog.get_logger()


class ApprovalTimeout(Exception):
    """Превышено время ожидания одобрения."""


async def request_approval(
    bus: MessageBus,
    request: ApprovalRequest,
    poll_interval: float = 2.0,
) -> ApprovalResult:
    """Отправить запрос на одобрение и ожидать ответ.

    Публикует запрос в канал approval:requests, затем опрашивает
    Redis каждые poll_interval секунд до получения результата
    или истечения timeout_minutes.
    """
    # Публикуем запрос — Telegram-бот подхватит
    await bus.publish("approval:requests", request.model_dump_json())
    logger.info(
        "approval_requested",
        request_id=request.id,
        action=request.action,
        agent_id=request.agent_id,
    )

    # Ожидаем результат
    max_polls = int(request.timeout_minutes * 60 / poll_interval)
    for _ in range(max_polls):
        result_json = await bus.get_approval_result(request.id)
        if result_json is not None:
            result = ApprovalResult.model_validate_json(result_json)
            logger.info(
                "approval_received",
                request_id=request.id,
                approved=result.approved,
                decided_by=result.decided_by,
            )
            return result
        await asyncio.sleep(poll_interval)

    logger.warning("approval_timeout", request_id=request.id)
    raise ApprovalTimeout(
        f"Одобрение {request.id} не получено за {request.timeout_minutes} мин"
    )


async def submit_approval_result(
    bus: MessageBus, result: ApprovalResult
) -> None:
    """Записать результат одобрения (вызывается Telegram-ботом)."""
    await bus.set_approval_result(result.request_id, result.model_dump_json())
    logger.info(
        "approval_submitted",
        request_id=result.request_id,
        approved=result.approved,
    )
