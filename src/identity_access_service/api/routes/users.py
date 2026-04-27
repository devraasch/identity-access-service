from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from identity_access_service.api.schemas import user as user_schemas
from identity_access_service.api.dependencies import Db, Settings
from identity_access_service.application import users as user_app
from identity_access_service.domain.errors import EmailAlreadyInUseError, UserNotFoundError

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=user_schemas.UserListResponse)
def get_user_collection(
    settings: Settings,
    db: Db,
    skip: int = Query(0, ge=0),
    limit: int | None = Query(None, ge=1),
) -> user_schemas.UserListResponse:
    if skip > settings.list_max_skip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="skip too large",
        )
    eff = limit if limit is not None else settings.list_default_limit
    if eff > settings.list_max_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit too large",
        )
    result = user_app.list_users(db, skip=skip, limit=eff)
    return user_schemas.UserListResponse(
        items=[user_schemas.UserOut.model_validate(x) for x in result.items],
        total=result.total,
        skip=skip,
        limit=eff,
    )


@router.post("", response_model=user_schemas.UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    db: Db,
    body: user_schemas.UserCreate,
) -> user_schemas.UserOut:
    try:
        row = user_app.create_user(
            db,
            email=body.email,
            password=body.password,
            full_name=body.full_name,
        )
    except EmailAlreadyInUseError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already in use",
        ) from None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return user_schemas.UserOut.model_validate(row)


@router.get("/{user_id}", response_model=user_schemas.UserOut)
def get_user(
    db: Db,
    user_id: uuid.UUID,
) -> user_schemas.UserOut:
    try:
        row = user_app.get_user(db, user_id)
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from None
    return user_schemas.UserOut.model_validate(row)


@router.patch("/{user_id}", response_model=user_schemas.UserOut)
def update_user(
    db: Db,
    user_id: uuid.UUID,
    body: user_schemas.UserUpdate,
) -> user_schemas.UserOut:
    data: dict[str, Any] = body.model_dump(exclude_unset=True)
    if not data:
        try:
            row = user_app.get_user(db, user_id)
        except UserNotFoundError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from None
        return user_schemas.UserOut.model_validate(row)
    try:
        row = user_app.update_user(
            db,
            user_id,
            email=data.get("email"),
            full_name=data.get("full_name"),
            password=data.get("password"),
            is_active=data.get("is_active"),
        )
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from None
    except EmailAlreadyInUseError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already in use",
        ) from None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return user_schemas.UserOut.model_validate(row)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_user(db: Db, user_id: uuid.UUID) -> None:
    try:
        user_app.deactivate_user(db, user_id)
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from None
