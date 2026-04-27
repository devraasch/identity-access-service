from __future__ import annotations

from fastapi import APIRouter

from identity_access_service.api.dependencies import Settings

router = APIRouter()


@router.get("/health")
def health(settings: Settings) -> dict[str, str | bool]:
    return {"status": "ok", "service": settings.app_name}
