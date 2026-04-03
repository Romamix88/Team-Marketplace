"""Агент-бухгалтер Wildberries."""

from __future__ import annotations

import asyncio
from pathlib import Path

from agents.base.agent import BaseAgent


class AccountantAgent(BaseAgent):
    """Бухгалтер — финансовые сверки, комиссии, штрафы."""

    def __init__(self) -> None:
        config_path = str(Path(__file__).parent / "config.yml")
        super().__init__(agent_id="agent-wb-accountant", config_path=config_path)


async def main() -> None:
    """Точка входа агента."""
    agent = AccountantAgent()
    await agent.start()


if __name__ == "__main__":
    asyncio.run(main())
