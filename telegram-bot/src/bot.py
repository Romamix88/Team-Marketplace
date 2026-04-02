"""Telegram-бот: одобрения, отчёты, команды управления."""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone

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
from shared.models import ApprovalRequest, ApprovalResult

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
        "Команда AI-агентов «Атмосфера» — Wildberries\n\n"
        "Доступные команды:\n"
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
        "/status — статус агентов\n"
        "/tasks — последние задачи\n"
        "/help — эта справка"
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


# --- Подписка на запросы одобрения ---

async def _approval_listener() -> None:
    """Фоновая задача: слушаем запросы на одобрение из Redis и отправляем в Telegram."""
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


# --- Запуск ---

async def main() -> None:
    """Точка входа Telegram-бота."""
    await bus.connect()
    logger.info("telegram_bot_starting")

    # Запускаем listener одобрений в фоне
    asyncio.create_task(_approval_listener())

    # Запускаем polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
