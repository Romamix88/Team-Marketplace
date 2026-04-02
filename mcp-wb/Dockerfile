FROM python:3.11-slim

WORKDIR /app

# Зависимости
COPY mcp-wb/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Общий код
COPY shared/ /app/shared/

# Код MCP-сервера (копируем как mcp_wb для корректных импортов)
COPY mcp-wb/ /app/mcp_wb/

ENV PYTHONPATH=/app
EXPOSE 8001

CMD ["uvicorn", "mcp_wb.src.server:app", "--host", "0.0.0.0", "--port", "8001"]
