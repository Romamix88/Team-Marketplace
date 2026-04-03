"""Агент-аналитик Wildberries."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from agents.base.agent import BaseAgent


class AnalystAgent(BaseAgent):
    """Аналитик — анализ продаж, маржинальности, рекомендации по ценам."""

    def __init__(self) -> None:
        config_path = str(Path(__file__).parent / "config.yml")
        super().__init__(agent_id="agent-wb-analyst", config_path=config_path)


async def main() -> None:
    """Точка входа агента."""
    agent = AnalystAgent()
    await agent.start()


if __name__ == "__main__":
    asyncio.run(main())
