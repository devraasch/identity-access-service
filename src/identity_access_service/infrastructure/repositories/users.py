from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from identity_access_service.infrastructure.models import User


def get(session: Session, user_id: uuid.UUID) -> User | None:
    return session.get(User, user_id)


def get_by_email(session: Session, email: str) -> User | None:
    stmt = select(User).where(User.email == email).limit(1)
    return session.execute(stmt).scalars().first()


def count_all(session: Session) -> int:
    return session.execute(select(func.count()).select_from(User)).scalar_one()


def list_page(session: Session, skip: int, limit: int) -> list[User]:
    stmt = select(User).order_by(User.created_at).offset(skip).limit(limit)
    return list(session.execute(stmt).scalars().all())
