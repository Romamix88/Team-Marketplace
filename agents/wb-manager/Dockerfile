FROM python:3.11-slim
WORKDIR /app
COPY agents/wb-manager/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY shared/ /app/shared/
COPY agents/__init__.py /app/agents/__init__.py
COPY agents/base/ /app/agents/base/
COPY agents/wb-manager/ /app/agents/wb_manager/
ENV PYTHONPATH=/app
CMD ["python", "-m", "agents.wb_manager.agent"]
