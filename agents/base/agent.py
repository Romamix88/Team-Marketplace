"""BaseAgent — базовый класс для всех AI-агентов."""

from __future__ import annotations

import asyncio
import json
import os
import signal
from pathlib import Path
from typing import Any

import structlog
import yaml

from shared.approval import ApprovalTimeout, request_approval
from shared.logging_config import setup_logging
from shared.message_bus import MessageBus
from shared.models import (
    AgentStatus,
    ApprovalRequest,
    Task,
    TaskStatus,
)
from shared.task_manager import TaskManager

from agents.base.tools import McpClient, RouterAIClient

logger = structlog.get_logger()

MAX_LLM_ITERATIONS = 10


class BaseAgent:
    """Базовый класс AI-агента для маркетплейсов."""

    def __init__(self, agent_id: str, config_path: str | None = None) -> None:
        self.agent_id = agent_id
        self._running = False

        # Загрузка конфигурации агента
        self._config = self._load_config(config_path)

        # Инициализация логирования
        setup_logging(component=agent_id)

        # Клиенты
        self._bus = MessageBus(
            os.getenv("REDIS_URL", "redis://redis:6379/0")
        )
        self._task_manager = TaskManager(self._bus)
        self._mcp = McpClient(
            mcp_url=os.getenv("MCP_WB_URL", "http://mcp-wb:8001"),
            agent_id=agent_id,
        )
        self._llm = RouterAIClient(
            api_key=os.getenv("ROUTERAI_API_KEY", ""),
            base_url=os.getenv("ROUTERAI_BASE_URL", "https://api.routerai.ru/v1"),
            model=self._config.get("model", "claude-sonnet-4-6"),
        )

        # Системный промпт
        self._system_prompt = self._load_system_prompt()

    def _load_config(self, config_path: str | None) -> dict[str, Any]:
        """Загрузить конфигурацию агента из YAML."""
        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                return yaml.safe_load(f) or {}
        return {}

    def _load_system_prompt(self) -> str:
        """Загрузить системный промпт агента."""
        prompt_path = self._config.get("system_prompt_path")
        if prompt_path and Path(prompt_path).exists():
            return Path(prompt_path).read_text(encoding="utf-8")
        return f"Ты AI-агент '{self.agent_id}' в команде управления маркетплейсом Wildberries компании «Атмосфера»."

    async def start(self) -> None:
        """Запуск основного цикла агента."""
        self._running = True
        await self._bus.connect()

        # Получаем доступные инструменты
        try:
            self._available_tools = await self._mcp.list_tools()
        except Exception:
            logger.warning("mcp_unavailable", agent_id=self.agent_id)
            self._available_tools = []

        logger.info(
            "agent_started",
            agent_id=self.agent_id,
            model=self._config.get("model"),
            tools_count=len(self._available_tools),
        )

        # Обработка SIGTERM для graceful shutdown
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._shutdown)

        # Основной цикл
        while self._running:
            try:
                await self._heartbeat()
                task = await self._bus.pop_task(self.agent_id, timeout=5)
                if task:
                    await self._execute_task(task)
            except Exception:
                logger.exception("agent_loop_error", agent_id=self.agent_id)
                await asyncio.sleep(1)

        # Cleanup
        await self._mcp.close()
        await self._llm.close()
        await self._bus.disconnect()
        logger.info("agent_stopped", agent_id=self.agent_id)

    def _shutdown(self) -> None:
        """Graceful shutdown."""
        logger.info("agent_shutting_down", agent_id=self.agent_id)
        self._running = False

    async def _heartbeat(self) -> None:
        """Отправить heartbeat в Redis."""
        status = AgentStatus(
            agent_id=self.agent_id,
            status="online",
            model=self._config.get("model"),
        )
        await self._bus.set_agent_status(status)

    async def _execute_task(self, task: Task) -> None:
        """Выполнить задачу с помощью LLM и MCP-инструментов."""
        logger.info("task_executing", task_id=task.id, task_type=task.type)

        # Обновляем статус
        await self._task_manager.update_status(task.id, TaskStatus.IN_PROGRESS)
        status = AgentStatus(
            agent_id=self.agent_id,
            status="busy",
            current_task_id=task.id,
            model=self._config.get("model"),
        )
        await self._bus.set_agent_status(status)

        try:
            # Если нужно одобрение — запрашиваем до выполнения
            if task.requires_approval:
                await self._request_task_approval(task)

            # LLM-цикл с инструментами
            result = await self._run_llm_loop(task)

            await self._task_manager.update_status(
                task.id, TaskStatus.COMPLETED, result=result
            )
            logger.info("task_completed", task_id=task.id)

        except ApprovalTimeout:
            await self._task_manager.update_status(
                task.id,
                TaskStatus.FAILED,
                error="Одобрение не получено в срок",
            )
        except Exception as exc:
            logger.exception("task_failed", task_id=task.id)
            await self._task_manager.update_status(
                task.id, TaskStatus.FAILED, error=str(exc)
            )

    async def _request_task_approval(self, task: Task) -> None:
        """Запросить одобрение для критичной операции."""
        await self._task_manager.update_status(
            task.id, TaskStatus.WAITING_APPROVAL
        )
        approval_req = ApprovalRequest(
            task_id=task.id,
            agent_id=self.agent_id,
            action=task.type,
            description=f"Агент {self.agent_id} запрашивает одобрение на: {task.type}",
            details=task.payload,
        )
        result = await request_approval(self._bus, approval_req)
        if not result.approved:
            raise Exception(f"Операция отклонена: {result.comment or 'без комментария'}")

    async def _run_llm_loop(self, task: Task) -> dict[str, Any]:
        """Цикл взаимодействия с LLM и вызовов инструментов."""
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._system_prompt},
            {
                "role": "user",
                "content": f"Задача: {task.type}\n\nДанные: {json.dumps(task.payload, ensure_ascii=False)}",
            },
        ]

        for iteration in range(MAX_LLM_ITERATIONS):
            response = await self._llm.chat(messages, tools=self._available_tools)
            choice = response["choices"][0]
            message = choice["message"]

            # Если LLM завершил (нет tool_calls)
            if choice.get("finish_reason") == "stop" or not message.get("tool_calls"):
                return {"response": message.get("content", ""), "iterations": iteration + 1}

            # Обработка tool_calls
            messages.append(message)
            for tool_call in message["tool_calls"]:
                fn = tool_call["function"]
                tool_name = fn["name"]
                tool_params = json.loads(fn["arguments"]) if isinstance(fn["arguments"], str) else fn["arguments"]

                logger.info("tool_calling", tool=tool_name, params=tool_params)
                result = await self._mcp.call_tool(tool_name, tool_params)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(result, ensure_ascii=False),
                })

        return {"response": "Превышен лимит итераций LLM", "iterations": MAX_LLM_ITERATIONS}
