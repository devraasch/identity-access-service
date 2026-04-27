from __future__ import annotations

from fastapi import FastAPI

from identity_access_service.api.routes import auth, health, users
from identity_access_service.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
    )
    app.include_router(health.router, tags=["health"])
    app.include_router(auth.router)
    app.include_router(users.router)
    return app


app = create_app()
