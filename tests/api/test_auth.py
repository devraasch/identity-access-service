def test_login_success(client, registered_user, tokens) -> None:
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"
    assert tokens["expires_in"] > 0


def test_login_wrong_password(client, registered_user) -> None:
    r = client.post(
        "/auth/login",
        json={"email": registered_user["email"], "password": "wrongpassword12"},
    )
    assert r.status_code == 401


def test_login_unknown_email(client) -> None:
    r = client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "irrelevant12"},
    )
    assert r.status_code == 401


def test_me_with_bearer(client, registered_user, tokens) -> None:
    r = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert r.status_code == 200
    assert r.json()["email"] == registered_user["email"]


def test_me_without_token(client) -> None:
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_refresh_success(client, tokens) -> None:
    r = client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert r.status_code == 200
    b = r.json()
    assert "access_token" in b
    assert b["expires_in"] > 0


def test_refresh_invalid(client) -> None:
    r = client.post(
        "/auth/refresh",
        json={"refresh_token": "invalid" * 8},
    )
    assert r.status_code == 401


def test_logout_revokes_refresh(client, tokens) -> None:
    r1 = client.post(
        "/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert r1.status_code == 204
    r2 = client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert r2.status_code == 401
