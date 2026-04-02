"""Клиенты к MCP-серверу и RouterAI (OpenAI-compatible)."""

from __future__ import annotations

import json
from typing import Any

import httpx
import structlog

logger = structlog.get_logger()


class McpClient:
    """HTTP-клиент к MCP-серверу."""

    def __init__(self, mcp_url: str, agent_id: str) -> None:
        self._mcp_url = mcp_url.rstrip("/")
        self._agent_id = agent_id
        self._client = httpx.AsyncClient(
            timeout=60.0,
            headers={"X-Agent-Id": agent_id},
        )

    async def list_tools(self) -> list[dict[str, Any]]:
        """Получить список доступных инструментов."""
        resp = await self._client.get(f"{self._mcp_url}/tools/list")
        resp.raise_for_status()
        return resp.json()

    async def call_tool(self, tool_name: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Вызвать инструмент MCP."""
        resp = await self._client.post(
            f"{self._mcp_url}/tools/call",
            json={"tool": tool_name, "params": params or {}},
        )
        resp.raise_for_status()
        result = resp.json()
        if not result.get("success"):
            logger.error("mcp_tool_error", tool=tool_name, error=result.get("error"))
        return result

    async def close(self) -> None:
        """Закрыть HTTP-клиент."""
        await self._client.aclose()


class RouterAIClient:
    """Клиент к RouterAI (OpenAI-compatible API)."""

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self._model = model
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=120.0,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Вызвать chat/completions с опциональным tool calling."""
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
        }
        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t.get("description", ""),
                        "parameters": t.get("parameters", {}),
                    },
                }
                for t in tools
            ]

        logger.debug("llm_request", model=self._model, messages_count=len(messages))
        resp = await self._client.post("/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
        logger.debug("llm_response", model=self._model, usage=data.get("usage"))
        return data

    async def close(self) -> None:
        """Закрыть HTTP-клиент."""
        await self._client.aclose()
