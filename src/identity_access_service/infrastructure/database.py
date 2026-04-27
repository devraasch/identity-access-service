from __future__ import annotations

from functools import lru_cache

from sqlalchemy import create_engine, pool
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from identity_access_service.core.config import get_settings

SessionFactory = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@lru_cache
def get_engine() -> Engine:
    s = get_settings()
    url = str(s.database_url)
    kwargs: dict = {
        "pool_pre_ping": True,
        "echo": s.debug,
    }
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if "memory" in url or url in ("sqlite://", "sqlite:///"):
            kwargs["poolclass"] = pool.StaticPool
    return create_engine(url, **kwargs)


def get_db():
    engine = get_engine()
    db = SessionFactory(bind=engine)
    try:
        yield db
    finally:
        db.close()
