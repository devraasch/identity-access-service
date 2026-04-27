from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from jwt import PyJWTError
from sqlalchemy.orm import Session

from identity_access_service.core.config import Settings
from identity_access_service.domain import user as user_domain
from identity_access_service.domain.errors import (
    InvalidCredentialsError,
    TokenInvalidError,
)
from identity_access_service.infrastructure import passwords
from identity_access_service.infrastructure.models import User
from identity_access_service.infrastructure.repositories import refresh_tokens as rt_repo
from identity_access_service.infrastructure.repositories import users as user_repo


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _hash_refresh(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def verify_password_and_get_user(
    session: Session,
    email: str,
    password: str,
    settings: Settings,
) -> User:
    email = user_domain.normalize_email(email)
    user = user_repo.get_by_email(session, email)
    if user is None or not user.is_active:
        raise InvalidCredentialsError
    if not passwords.verify_password(password, user.password_hash):
        raise InvalidCredentialsError
    return user


def issue_tokens(
    session: Session,
    user: User,
    settings: Settings,
) -> tuple[str, str, int]:
    now = _utcnow()
    exp_access = now + timedelta(minutes=settings.access_token_expire_minutes)
    exp_refresh = now + timedelta(days=settings.refresh_token_expire_days)
    exp_ts = int(exp_access.timestamp())
    payload = {
        "sub": str(user.id),
        "typ": "access",
        "exp": exp_ts,
        "iat": int(now.timestamp()),
    }
    secret = settings.jwt_secret.get_secret_value()
    access = jwt.encode(
        payload,
        secret,
        algorithm=settings.jwt_algorithm,
    )
    if isinstance(access, bytes):
        access = access.decode("utf-8")
    raw_refresh = secrets.token_urlsafe(48)
    h = _hash_refresh(raw_refresh)
    rt_repo.create(
        session,
        user_id=user.id,
        token_hash=h,
        expires_at=exp_refresh,
    )
    session.commit()
    ttl = int((exp_access - now).total_seconds())
    return access, raw_refresh, ttl


def subject_from_access_token(token: str, settings: Settings) -> uuid.UUID:
    secret = settings.jwt_secret.get_secret_value()
    try:
        data = jwt.decode(
            token,
            secret,
            algorithms=[settings.jwt_algorithm],
        )
    except PyJWTError as e:
        raise TokenInvalidError from e
    if data.get("typ") != "access":
        raise TokenInvalidError
    sub = data.get("sub")
    if not sub:
        raise TokenInvalidError
    return uuid.UUID(str(sub))


def refresh_access_token(
    session: Session,
    refresh_token: str,
    settings: Settings,
) -> tuple[str, int]:
    h = _hash_refresh(refresh_token)
    row = rt_repo.get_active_by_hash(session, h)
    if row is None:
        raise TokenInvalidError
    if _as_utc(row.expires_at) < _utcnow():
        raise TokenInvalidError
    user = user_repo.get(session, row.user_id)
    if user is None or not user.is_active:
        raise TokenInvalidError
    now = _utcnow()
    exp_access = now + timedelta(minutes=settings.access_token_expire_minutes)
    exp_ts = int(exp_access.timestamp())
    payload = {
        "sub": str(user.id),
        "typ": "access",
        "exp": exp_ts,
        "iat": int(now.timestamp()),
    }
    secret = settings.jwt_secret.get_secret_value()
    access = jwt.encode(
        payload,
        secret,
        algorithm=settings.jwt_algorithm,
    )
    if isinstance(access, bytes):
        access = access.decode("utf-8")
    ttl = int((exp_access - now).total_seconds())
    return access, ttl


def logout(session: Session, refresh_token: str) -> bool:
    h = _hash_refresh(refresh_token)
    n = rt_repo.revoke_by_hash(session, h)
    session.commit()
    return n > 0
