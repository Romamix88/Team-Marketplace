FROM python:3.11-slim
WORKDIR /app
COPY agents/wb-content/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY shared/ /app/shared/
COPY agents/__init__.py /app/agents/__init__.py
COPY agents/base/ /app/agents/base/
COPY agents/wb-content/ /app/agents/wb_content/
ENV PYTHONPATH=/app
CMD ["python", "-m", "agents.wb_content.agent"]
