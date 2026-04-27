from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from identity_access_service.application import auth as auth_app
from identity_access_service.core import config
from identity_access_service.domain.errors import TokenInvalidError
from identity_access_service.infrastructure.database import get_db
from identity_access_service.infrastructure.models import User
from identity_access_service.infrastructure.repositories import users as user_repo

Settings = Annotated[config.Settings, Depends(config.get_settings)]
Db = Annotated[Session, Depends(get_db)]
Bearer = HTTPBearer(auto_error=False)


def get_current_user(
    db: Db,
    settings: Settings,
    cred: HTTPAuthorizationCredentials | None = Depends(Bearer),
) -> User:
    if cred is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        uid = auth_app.subject_from_access_token(cred.credentials, settings)
    except TokenInvalidError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from None
    u = user_repo.get(db, uid)
    if u is None or not u.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return u


CurrentUser = Annotated[User, Depends(get_current_user)]
