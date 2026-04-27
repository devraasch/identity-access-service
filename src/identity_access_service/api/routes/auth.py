from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from identity_access_service.api.schemas import auth as auth_schemas
from identity_access_service.api.schemas import user as user_schemas
from identity_access_service.api.dependencies import CurrentUser, Db, Settings
from identity_access_service.application import auth as auth_app
from identity_access_service.domain.errors import InvalidCredentialsError, TokenInvalidError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=auth_schemas.TokenOut)
def login(
    db: Db,
    settings: Settings,
    body: auth_schemas.LoginIn,
) -> auth_schemas.TokenOut:
    try:
        user = auth_app.verify_password_and_get_user(
            db, body.email, body.password, settings
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        ) from None
    access, refresh, ttl = auth_app.issue_tokens(db, user, settings)
    return auth_schemas.TokenOut(
        access_token=access,
        refresh_token=refresh,
        expires_in=ttl,
    )


@router.post("/refresh", response_model=auth_schemas.RefreshOut)
def refresh(
    db: Db,
    settings: Settings,
    body: auth_schemas.RefreshIn,
) -> auth_schemas.RefreshOut:
    try:
        access, ttl = auth_app.refresh_access_token(
            db, body.refresh_token, settings
        )
    except TokenInvalidError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from None
    return auth_schemas.RefreshOut(access_token=access, expires_in=ttl)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    db: Db,
    body: auth_schemas.LogoutIn,
) -> None:
    auth_app.logout(db, body.refresh_token)


@router.get("/me", response_model=user_schemas.UserOut)
def me(user: CurrentUser) -> user_schemas.UserOut:
    return user_schemas.UserOut.model_validate(user)
