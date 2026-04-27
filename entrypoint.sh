#!/bin/sh
set -e
cd /app
/app/.venv/bin/alembic upgrade head
exec /app/.venv/bin/gunicorn identity_access_service.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 1 --access-logfile - --error-logfile -
