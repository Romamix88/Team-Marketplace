"""Разграничение доступа агентов к модулям MCP-сервера WB."""

from __future__ import annotations

import structlog

logger = structlog.get_logger()

# Какие модули доступны каждому агенту
AGENT_ACCESS: dict[str, list[str]] = {
    "agent-wb-logistics": ["warehouses", "analytics"],
    "agent-wb-content": ["content", "analytics"],
    "agent-wb-marketing": ["advertising", "analytics"],
    "agent-wb-analyst": ["analytics", "prices", "finance"],
    "agent-wb-accountant": ["finance", "analytics"],
    "agent-wb-manager": [
        "warehouses", "content", "prices",
        "advertising", "analytics", "finance",
    ],
}


def check_access(agent_id: str, module: str) -> bool:
    """Проверить, имеет ли агент доступ к модулю."""
    allowed = AGENT_ACCESS.get(agent_id, [])
    has_access = module in allowed
    if not has_access:
        logger.warning(
            "access_denied",
            agent_id=agent_id,
            module=module,
            allowed_modules=allowed,
        )
    return has_access


def get_allowed_modules(agent_id: str) -> list[str]:
    """Получить список разрешённых модулей для агента."""
    return AGENT_ACCESS.get(agent_id, [])


def filter_tools(agent_id: str, all_tools: list[dict]) -> list[dict]:
    """Отфильтровать инструменты по доступу агента."""
    allowed_modules = get_allowed_modules(agent_id)
    return [t for t in all_tools if t.get("module") in allowed_modules]
