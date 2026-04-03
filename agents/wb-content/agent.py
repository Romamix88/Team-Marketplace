"""Агент контент-менеджер Wildberries."""

from __future__ import annotations

import asyncio
from pathlib import Path

from agents.base.agent import BaseAgent


class ContentAgent(BaseAgent):
    """Контент-менеджер — карточки товаров, SEO, A/B тесты."""

    def __init__(self) -> None:
        config_path = str(Path(__file__).parent / "config.yml")
        super().__init__(agent_id="agent-wb-content", config_path=config_path)


async def main() -> None:
    """Точка входа агента."""
    agent = ContentAgent()
    await agent.start()


if __name__ == "__main__":
    asyncio.run(main())
