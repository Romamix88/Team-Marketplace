"""Telegram-бот: чат с руководителем, одобрения, отчёты, команды."""

from __future__ import annotations

import asyncio
import json
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import structlog

from shared.approval import submit_approval_result
from shared.logging_config import setup_logging
from shared.message_bus import MessageBus
from shared.models import ApprovalRequest, ApprovalResult, Task, TaskStatus
from shared.task_manager import TaskManager

setup_logging(component="telegram-bot")
logger = structlog.get_logger()

# Конфигурация
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
MCP_WB_URL = os.getenv("MCP_WB_URL", "http://mcp-wb:8001")

# Whitelist разрешённых chat_id
ALLOWED_CHAT_IDS: set[str] = set(
    cid.strip() for cid in ADMIN_CHAT_ID.split(",") if cid.strip()
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
bus = MessageBus(REDIS_URL)
task_mgr: TaskManager | None = None


# --- Middleware: проверка доступа ---

def _is_authorized(chat_id: int) -> bool:
    """Проверить, авторизован ли пользователь."""
    return str(chat_id) in ALLOWED_CHAT_IDS


# --- Команды ---

@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Приветственное сообщение."""
    if not _is_authorized(message.chat.id):
        await message.answer("Доступ запрещён.")
        return
    await message.answer(
        "👋 Команда AI-агентов «Атмосфера» — Wildberries\n\n"
        "Просто напишите сообщение — руководитель команды ответит.\n\n"
        "Команды:\n"
        "/status — статус агентов\n"
        "/tasks — последние задачи\n"
        "/help — справка"
    )


@dp.message(Command("status"))
async def cmd_status(message: Message) -> None:
    """Статус всех агентов."""
    if not _is_authorized(message.chat.id):
        return
    agents = await bus.get_all_agents()
    if not agents:
        await message.answer("Нет активных агентов.")
        return

    lines = ["**Статус агентов:**\n"]
    for a in agents:
        icon = {"online": "🟢", "busy": "🟡", "offline": "🔴", "error": "❌"}.get(
            a.status, "⚪"
        )
        lines.append(f"{icon} `{a.agent_id}` — {a.status}")
        if a.current_task_id:
            lines.append(f"   Задача: `{a.current_task_id[:8]}...`")
    await message.answer("\n".join(lines), parse_mode="Markdown")


@dp.message(Command("tasks"))
async def cmd_tasks(message: Message) -> None:
    """Последние задачи."""
    if not _is_authorized(message.chat.id):
        return
    tasks = await bus.get_recent_tasks(limit=10)
    if not tasks:
        await message.answer("Нет задач.")
        return

    lines = ["**Последние задачи:**\n"]
    for t in tasks:
        icon = {
            "completed": "✅",
            "failed": "❌",
            "in_progress": "🔄",
            "pending": "⏳",
            "waiting_approval": "🔔",
        }.get(t.status.value, "❓")
        lines.append(f"{icon} `{t.id[:8]}` | {t.type} → {t.assigned_to}")
    await message.answer("\n".join(lines), parse_mode="Markdown")


@dp.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Справка."""
    if not _is_authorized(message.chat.id):
        return
    await message.answer(
        "Просто напишите сообщение — руководитель команды обработает.\n\n"
        "/status — статус агентов\n"
        "/tasks — последние задачи\n"
        "/help — эта справка"
    )


# --- Обработка свободных сообщений → задача руководителю ---

@dp.message(F.text)
async def handle_free_message(message: Message) -> None:
    """Свободное сообщение от владельца → задача руководителю-агенту."""
    if not _is_authorized(message.chat.id):
        return

    assert task_mgr is not None

    # Отправляем «печатает...»
    await message.answer("⏳ Передаю руководителю команды...")

    # Создаём задачу для руководителя
    task = await task_mgr.create_and_assign(
        task_type="owner_message",
        assigned_to="agent-wb-manager",
        payload={
            "message": message.text,
            "chat_id": message.chat.id,
            "from_user": message.from_user.full_name if message.from_user else "owner",
        },
        created_by="telegram-bot",
        priority=1,
    )

    logger.info(
        "owner_message_sent",
        task_id=task.id,
        message_preview=message.text[:100],
    )


# --- Обработка одобрений ---

@dp.callback_query(F.data.startswith("approve:") | F.data.startswith("reject:"))
async def handle_approval(callback: CallbackQuery) -> None:
    """Обработка одобрения/отклонения через inline-кнопки."""
    if not _is_authorized(callback.message.chat.id):
        await callback.answer("Доступ запрещён")
        return

    parts = callback.data.split(":", 1)
    if len(parts) != 2:
        await callback.answer("Ошибка данных")
        return

    action, request_id = parts
    approved = action == "approve"

    result = ApprovalResult(
        request_id=request_id,
        approved=approved,
        decided_by=f"tg:{callback.from_user.id}:{callback.from_user.full_name}",
    )
    await submit_approval_result(bus, result)

    status_text = "✅ Одобрено" if approved else "❌ Отклонено"
    await callback.message.edit_text(
        f"{callback.message.text}\n\n{status_text} — {callback.from_user.full_name}"
    )
    await callback.answer(status_text)
    logger.info(
        "approval_handled",
        request_id=request_id,
        approved=approved,
        user=callback.from_user.full_name,
    )


# --- Фоновые слушатели ---

async def _approval_listener() -> None:
    """Слушаем запросы на одобрение из Redis → отправляем в Telegram."""
    pubsub = bus.redis.pubsub()
    await pubsub.subscribe("approval:requests")
    logger.info("approval_listener_started")

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue
        try:
            req = ApprovalRequest.model_validate_json(message["data"])
            text = (
                f"🔔 **Запрос на одобрение**\n\n"
                f"Агент: `{req.agent_id}`\n"
                f"Действие: {req.action}\n"
                f"Описание: {req.description}\n"
            )
            if req.details:
                details_str = json.dumps(req.details, ensure_ascii=False, indent=2)
                text += f"\nДетали:\n```\n{details_str}\n```"

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Одобрить", callback_data=f"approve:{req.id}"
                        ),
                        InlineKeyboardButton(
                            text="❌ Отклонить", callback_data=f"reject:{req.id}"
                        ),
                    ]
                ]
            )

            for chat_id in ALLOWED_CHAT_IDS:
                await bot.send_message(
                    int(chat_id), text, reply_markup=keyboard, parse_mode="Markdown"
                )
            logger.info("approval_sent_to_telegram", request_id=req.id)

        except Exception:
            logger.exception("approval_listener_error")


async def _response_listener() -> None:
    """Слушаем ответы от руководителя → отправляем в Telegram."""
    pubsub = bus.redis.pubsub()
    await pubsub.subscribe("manager:responses")
    logger.info("response_listener_started")

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue
        try:
            data = json.loads(message["data"])
            chat_id = data.get("chat_id")
            text = data.get("text", "")

            if chat_id and text:
                # Telegram ограничивает сообщение 4096 символами
                for i in range(0, len(text), 4000):
                    chunk = text[i:i + 4000]
                    await bot.send_message(int(chat_id), chunk)

                logger.info("manager_response_sent", chat_id=chat_id, length=len(text))

        except Exception:
            logger.exception("response_listener_error")


async def _task_completion_listener() -> None:
    """Слушаем завершённые задачи owner_message → отправляем результат в Telegram."""
    while True:
        try:
            # Проверяем последние задачи на завершённые owner_message
            recent_tasks = await bus.get_recent_tasks(limit=20)
            for task in recent_tasks:
                if (
                    task.type == "owner_message"
                    and task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
                    and task.payload.get("chat_id")
                ):
                    # Проверяем, не отправляли ли мы уже этот ответ
                    sent_key = f"response_sent:{task.id}"
                    already_sent = await bus.redis.get(sent_key)
                    if already_sent:
                        continue

                    chat_id = task.payload["chat_id"]

                    if task.status == TaskStatus.COMPLETED and task.result:
                        text = task.result.get("response", "Задача выполнена.")
                    elif task.status == TaskStatus.FAILED:
                        text = f"❌ Ошибка: {task.error or 'Неизвестная ошибка'}"
                    else:
                        continue

                    # Отправляем ответ
                    for i in range(0, len(text), 4000):
                        chunk = text[i:i + 4000]
                        await bot.send_message(int(chat_id), chunk)

                    # Помечаем как отправленное
                    await bus.redis.set(sent_key, "1", ex=86400)
                    logger.info("task_response_sent", task_id=task.id, chat_id=chat_id)

        except Exception:
            logger.exception("task_completion_listener_error")

        await asyncio.sleep(2)  # Проверяем каждые 2 секунды


# --- Запуск ---

async def main() -> None:
    """Точка входа Telegram-бота."""
    global task_mgr

    await bus.connect()
    task_mgr = TaskManager(bus)
    logger.info("telegram_bot_starting")

    # Запускаем фоновые слушатели
    asyncio.create_task(_approval_listener())
    asyncio.create_task(_response_listener())
    asyncio.create_task(_task_completion_listener())

    # Запускаем polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
