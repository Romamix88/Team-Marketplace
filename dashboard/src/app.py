"""Веб-дашборд: статус агентов, задачи, здоровье системы."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import structlog

from shared.logging_config import setup_logging
from shared.message_bus import MessageBus
from shared.task_manager import TaskManager

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

bus = MessageBus(REDIS_URL)
task_mgr = TaskManager(bus)

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(component="dashboard")
    await bus.connect()
    structlog.get_logger().info("dashboard_started")
    yield
    await bus.disconnect()


app = FastAPI(title="Atmosfera Dashboard", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Главная страница дашборда."""
    agents = await bus.get_all_agents()
    tasks = await task_mgr.get_recent_tasks(limit=20)
    return templates.TemplateResponse(
        name="index.html",
        context={"request": request, "agents": agents, "tasks": tasks},
    )


@app.get("/api/agents", response_class=HTMLResponse)
async def agents_partial(request: Request) -> HTMLResponse:
    """HTMX-фрагмент: список агентов."""
    agents = await bus.get_all_agents()
    rows = ""
    for a in agents:
        icon = {"online": "🟢", "busy": "🟡", "offline": "🔴", "error": "❌"}.get(
            a.status, "⚪"
        )
        task_cell = a.current_task_id[:8] + "..." if a.current_task_id else "—"
        rows += (
            f"<tr><td>{icon}</td><td>{a.agent_id}</td>"
            f"<td>{a.status}</td><td>{a.model or '—'}</td>"
            f"<td>{task_cell}</td></tr>\n"
        )
    return HTMLResponse(rows or "<tr><td colspan='5'>Нет активных агентов</td></tr>")


@app.get("/api/tasks", response_class=HTMLResponse)
async def tasks_partial(request: Request) -> HTMLResponse:
    """HTMX-фрагмент: последние задачи."""
    tasks = await task_mgr.get_recent_tasks(limit=15)
    icons = {
        "completed": "✅", "failed": "❌", "in_progress": "🔄",
        "pending": "⏳", "waiting_approval": "🔔",
    }
    rows = ""
    for t in tasks:
        icon = icons.get(t.status.value, "❓")
        rows += (
            f"<tr><td>{icon}</td><td>{t.id[:8]}</td>"
            f"<td>{t.type}</td><td>{t.assigned_to}</td>"
            f"<td>{t.status.value}</td></tr>\n"
        )
    return HTMLResponse(rows or "<tr><td colspan='5'>Нет задач</td></tr>")


@app.get("/health")
async def health() -> dict:
    """Проверка состояния."""
    return {"status": "ok", "component": "dashboard"}
