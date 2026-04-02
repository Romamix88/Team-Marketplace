FROM python:3.11-slim

WORKDIR /app

# Зависимости
COPY dashboard/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Общий код
COPY shared/ /app/shared/

# Код дашборда
COPY dashboard/ /app/dashboard/

ENV PYTHONPATH=/app
EXPOSE 8080

CMD ["uvicorn", "dashboard.src.app:app", "--host", "0.0.0.0", "--port", "8080"]
