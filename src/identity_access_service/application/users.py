from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from identity_access_service.core.config import get_settings
from identity_access_service.domain import user as user_domain
from identity_access_service.domain.errors import EmailAlreadyInUseError, UserNotFoundError
from identity_access_service.infrastructure.models import User
from identity_access_service.infrastructure import passwords
from identity_access_service.infrastructure.repositories import users as user_repo


@dataclass(frozen=True, slots=True)
class UserListResult:
    items: list[User]
    total: int


def _require_user(row: User | None) -> User:
    if row is None:
        raise UserNotFoundError
    return row


def create_user(
    session: Session,
    *,
    email: str,
    password: str,
    full_name: str,
) -> User:
    settings = get_settings()
    if len(password) < settings.min_password_length:
        msg = f"Password must be at least {settings.min_password_length} characters"
        raise ValueError(msg)
    name = full_name.strip()
    if not name or len(name) > settings.max_name_length:
        raise ValueError("Invalid name")

    email = user_domain.normalize_email(email)
    u = User(
        email=email,
        full_name=name,
        password_hash=passwords.hash_password(password),
        is_active=True,
    )
    session.add(u)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise EmailAlreadyInUseError from None
    session.refresh(u)
    return u


def get_user(session: Session, user_id: uuid.UUID) -> User:
    return _require_user(user_repo.get(session, user_id))


def list_users(
    session: Session,
    *,
    skip: int = 0,
    limit: int = 100,
) -> UserListResult:
    total = user_repo.count_all(session)
    items = user_repo.list_page(session, skip, limit)
    return UserListResult(items=items, total=total)


def update_user(
    session: Session,
    user_id: uuid.UUID,
    *,
    email: str | None = None,
    full_name: str | None = None,
    password: str | None = None,
    is_active: bool | None = None,
) -> User:
    settings = get_settings()
    user = _require_user(user_repo.get(session, user_id))
    if email is not None:
        user.email = user_domain.normalize_email(email)
    if full_name is not None:
        name = full_name.strip()
        if not name or len(name) > settings.max_name_length:
            raise ValueError("Invalid name")
        user.full_name = name
    if password is not None:
        if len(password) < settings.min_password_length:
            msg = f"Password must be at least {settings.min_password_length} characters"
            raise ValueError(msg)
        user.password_hash = passwords.hash_password(password)
    if is_active is not None:
        user.is_active = is_active
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise EmailAlreadyInUseError from None
    session.refresh(user)
    return user


def deactivate_user(session: Session, user_id: uuid.UUID) -> None:
    user = _require_user(user_repo.get(session, user_id))
    if not user.is_active:
        return
    user.is_active = False
    session.add(user)
    session.commit()
