FROM python:3.11-slim

WORKDIR /app

# Зависимости агента
COPY agents/wb-analyst/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Общий код
COPY shared/ /app/shared/

# Базовый класс агента
COPY agents/__init__.py /app/agents/__init__.py
COPY agents/base/ /app/agents/base/

# Код агента
COPY agents/wb-analyst/ /app/agents/wb_analyst/

ENV PYTHONPATH=/app

CMD ["python", "-m", "agents.wb_analyst.agent"]
