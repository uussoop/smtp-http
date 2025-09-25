FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN adduser --disabled-password --gecos "" appuser && chown -R appuser:appuser /app

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm -f /tmp/requirements.txt

COPY smtp_sanic /app

USER appuser

EXPOSE 8000

CMD ["python", "-m", "sanic", "smtp_sanic.app:app", "--host=0.0.0.0", "--port=8000", "--access-logs"]


