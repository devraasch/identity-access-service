import os

os.environ["IAC_DATABASE_URL"] = "sqlite://"
os.environ["IAC_DEBUG"] = "true"
os.environ["IAC_APP_NAME"] = "identity-access-service"
os.environ["IAC_JWT_SECRET"] = "test-jwt-secret-must-be-long-enough-for-hs256-key-material"

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from identity_access_service.core import config
    from identity_access_service.infrastructure import database
    from identity_access_service.infrastructure.database import SessionFactory, get_db, get_engine
    from identity_access_service.infrastructure.models.base import Base
    from identity_access_service.main import app

    config.get_settings.cache_clear()
    database.get_engine.cache_clear()
    engine = get_engine()
    Base.metadata.create_all(engine)

    def override_db():
        s = SessionFactory(bind=engine)
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as t:
        yield t
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    database.get_engine.cache_clear()
    config.get_settings.cache_clear()


@pytest.fixture
def user_payload():
    return {
        "email": "u@example.com",
        "password": "password12",
        "full_name": "Test User",
    }


@pytest.fixture
def registered_user(client, user_payload):
    r = client.post("/users", json=user_payload)
    assert r.status_code == 201
    return {**user_payload, "id": r.json()["id"]}


@pytest.fixture
def tokens(client, registered_user):
    r = client.post(
        "/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert r.status_code == 200
    b = r.json()
    return b
