"""MCP-сервер Wildberries — точка входа (FastAPI)."""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

# Добавляем корень проекта в sys.path для импорта shared
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from shared.logging_config import setup_logging
from shared.models import ToolCallRequest, ToolCallResponse

from mcp_wb.src.auth.access import check_access, filter_tools
from mcp_wb.src.modules.analytics import (
    ANALYTICS_HANDLERS,
    ANALYTICS_TOOLS,
    get_nm_report,
    get_orders,
    get_sales,
    get_stocks,
)
from mcp_wb.src.modules.warehouses import (
    WAREHOUSE_HANDLERS,
    WAREHOUSE_TOOLS,
)
from mcp_wb.src.wb_client import WBClient, WBApiError

import structlog

logger = structlog.get_logger()

# Глобальный клиент WB
_wb_client: WBClient | None = None

# Объединённый реестр инструментов и обработчиков
ALL_TOOLS = ANALYTICS_TOOLS + WAREHOUSE_TOOLS
ALL_HANDLERS: dict[str, Any] = {**ANALYTICS_HANDLERS, **WAREHOUSE_HANDLERS}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения."""
    global _wb_client
    setup_logging(component="mcp-wb")
    _wb_client = WBClient()
    logger.info("mcp_wb_started", tools_count=len(ALL_TOOLS))
    yield
    if _wb_client:
        await _wb_client.close()
    logger.info("mcp_wb_stopped")


app = FastAPI(title="MCP-WB Server", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, Any]:
    """Проверка состояния сервера."""
    return {
        "status": "ok",
        "modules": ["analytics", "warehouses"],
        "tools_count": len(ALL_TOOLS),
    }


@app.get("/tools/list")
async def list_tools(
    x_agent_id: str = Header(default="", alias="X-Agent-Id"),
) -> list[dict]:
    """Список доступных инструментов (фильтрация по агенту)."""
    if not x_agent_id:
        return ALL_TOOLS
    return filter_tools(x_agent_id, ALL_TOOLS)


@app.post("/tools/call")
async def call_tool(
    body: ToolCallRequest,
    x_agent_id: str = Header(default="", alias="X-Agent-Id"),
) -> ToolCallResponse:
    """Вызов инструмента MCP."""
    handler = ALL_HANDLERS.get(body.tool)
    if handler is None:
        return ToolCallResponse(
            success=False, error=f"Инструмент '{body.tool}' не найден"
        )

    # Проверка доступа
    tool_def = next((t for t in ALL_TOOLS if t["name"] == body.tool), None)
    if tool_def and x_agent_id:
        module = tool_def.get("module", "")
        if not check_access(x_agent_id, module):
            return ToolCallResponse(
                success=False,
                error=f"Доступ запрещён: агент '{x_agent_id}' не имеет доступа к модулю '{module}'",
            )

    # Вызов обработчика
    try:
        assert _wb_client is not None
        result = await handler(client=_wb_client, **body.params)
        logger.info(
            "tool_called",
            tool=body.tool,
            agent_id=x_agent_id,
            success=True,
        )
        return ToolCallResponse(success=True, data=result)
    except WBApiError as exc:
        logger.error(
            "tool_wb_error",
            tool=body.tool,
            status=exc.status_code,
            detail=exc.detail,
        )
        return ToolCallResponse(success=False, error=str(exc))
    except Exception as exc:
        logger.exception("tool_error", tool=body.tool)
        return ToolCallResponse(success=False, error=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
