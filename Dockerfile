FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH=/app/src

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir "uv"

COPY pyproject.toml uv.lock README.md alembic.ini entrypoint.sh ./
COPY alembic ./alembic
COPY src ./src

RUN uv sync --frozen --no-dev && chmod +x /app/entrypoint.sh

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
