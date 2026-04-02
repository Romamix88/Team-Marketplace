FROM python:3.11-slim

WORKDIR /app

# Зависимости
COPY telegram-bot/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Общий код
COPY shared/ /app/shared/

# Код бота
COPY telegram-bot/ /app/telegram_bot/

ENV PYTHONPATH=/app

CMD ["python", "-m", "telegram_bot.src.bot"]
