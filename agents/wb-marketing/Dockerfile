FROM python:3.11-slim
WORKDIR /app
COPY agents/wb-marketing/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY shared/ /app/shared/
COPY agents/__init__.py /app/agents/__init__.py
COPY agents/base/ /app/agents/base/
COPY agents/wb-marketing/ /app/agents/wb_marketing/
ENV PYTHONPATH=/app
CMD ["python", "-m", "agents.wb_marketing.agent"]
