"""Redis-шина сообщений: очереди задач, pub/sub, shared state."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable

import redis.asyncio as aioredis
import structlog

from shared.models import AgentStatus, Task

logger = structlog.get_logger()


class MessageBus:
    """Центральная шина сообщений на базе Redis."""

    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url
        self._redis: aioredis.Redis | None = None
        self._pubsub: aioredis.client.PubSub | None = None

    async def connect(self) -> None:
        """Подключение к Redis."""
        self._redis = aioredis.from_url(
            self._redis_url, decode_responses=True
        )
        await self._redis.ping()
        logger.info("redis_connected", url=self._redis_url)

    async def disconnect(self) -> None:
        """Отключение от Redis."""
        if self._pubsub:
            await self._pubsub.close()
        if self._redis:
            await self._redis.close()
        logger.info("redis_disconnected")

    @property
    def redis(self) -> aioredis.Redis:
        """Доступ к клиенту Redis."""
        if self._redis is None:
            raise RuntimeError("MessageBus не подключён. Вызовите connect().")
        return self._redis

    # --- Очереди задач ---

    async def push_task(self, agent_id: str, task: Task) -> None:
        """Добавить задачу в очередь агента."""
        queue = f"tasks:{agent_id}"
        await self.redis.rpush(queue, task.model_dump_json())
        await self.store_task(task)
        # Обновляем список последних задач
        await self.redis.lpush("tasks:recent", task.id)
        await self.redis.ltrim("tasks:recent", 0, 99)
        logger.info("task_pushed", agent_id=agent_id, task_id=task.id, task_type=task.type)

    async def pop_task(self, agent_id: str, timeout: int = 5) -> Task | None:
        """Получить задачу из очереди (блокирующее ожидание)."""
        queue = f"tasks:{agent_id}"
        result = await self.redis.blpop(queue, timeout=timeout)
        if result is None:
            return None
        _, data = result
        task = Task.model_validate_json(data)
        logger.info("task_popped", agent_id=agent_id, task_id=task.id)
        return task

    # --- Хранение задач ---

    async def store_task(self, task: Task) -> None:
        """Сохранить/обновить задачу в Redis."""
        key = f"task:{task.id}"
        await self.redis.set(key, task.model_dump_json(), ex=86400)  # TTL 24ч

    async def get_task(self, task_id: str) -> Task | None:
        """Получить задачу по ID."""
        data = await self.redis.get(f"task:{task_id}")
        if data is None:
            return None
        return Task.model_validate_json(data)

    async def get_recent_task_ids(self, limit: int = 50) -> list[str]:
        """Получить ID последних задач."""
        return await self.redis.lrange("tasks:recent", 0, limit - 1)

    async def get_recent_tasks(self, limit: int = 50) -> list[Task]:
        """Получить последние задачи с данными."""
        task_ids = await self.get_recent_task_ids(limit)
        tasks: list[Task] = []
        for task_id in task_ids:
            task = await self.get_task(task_id)
            if task:
                tasks.append(task)
        return tasks

    # --- Статусы агентов ---

    async def set_agent_status(self, status: AgentStatus) -> None:
        """Обновить статус агента."""
        key = f"agents:{status.agent_id}"
        # Фильтруем None-значения — Redis HSET не принимает None
        data = {k: v for k, v in json.loads(status.model_dump_json()).items() if v is not None}
        await self.redis.hset(key, mapping=data)
        await self.redis.sadd("agents:all", status.agent_id)
        await self.redis.expire(key, 300)  # TTL 5 мин (heartbeat обновляет)

    async def get_agent_status(self, agent_id: str) -> AgentStatus | None:
        """Получить статус агента."""
        data = await self.redis.hgetall(f"agents:{agent_id}")
        if not data:
            return None
        return AgentStatus.model_validate(data)

    async def get_all_agents(self) -> list[AgentStatus]:
        """Получить статусы всех агентов."""
        agent_ids = await self.redis.smembers("agents:all")
        agents: list[AgentStatus] = []
        for agent_id in agent_ids:
            status = await self.get_agent_status(agent_id)
            if status:
                agents.append(status)
        return agents

    # --- Pub/Sub ---

    async def publish(self, channel: str, message: str) -> None:
        """Опубликовать сообщение в канал."""
        await self.redis.publish(channel, message)
        logger.debug("message_published", channel=channel)

    async def subscribe(
        self, channel: str, callback: Callable[[str], Any]
    ) -> None:
        """Подписаться на канал и вызывать callback при новых сообщениях."""
        self._pubsub = self.redis.pubsub()
        await self._pubsub.subscribe(channel)
        logger.info("subscribed", channel=channel)

        async for message in self._pubsub.listen():
            if message["type"] == "message":
                try:
                    await callback(message["data"])
                except Exception:
                    logger.exception("pubsub_callback_error", channel=channel)

    # --- Approval ---

    async def set_approval_result(self, request_id: str, result_json: str) -> None:
        """Записать результат одобрения."""
        key = f"approval:result:{request_id}"
        await self.redis.set(key, result_json, ex=3600)  # TTL 1 час

    async def get_approval_result(self, request_id: str) -> str | None:
        """Получить результат одобрения."""
        return await self.redis.get(f"approval:result:{request_id}")
