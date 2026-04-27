def test_create_user_does_not_expose_secrets(client, user_payload) -> None:
    r = client.post("/users", json=user_payload)
    assert r.status_code == 201
    body = r.json()
    assert "password" not in body
    assert "password_hash" not in body


def test_list_users_pagination(client, registered_user) -> None:
    r = client.get("/users")
    assert r.status_code == 200
    d = r.json()
    assert d["total"] == 1
    assert len(d["items"]) == 1


def test_deactivate_user(client, registered_user) -> None:
    uid = registered_user["id"]
    r = client.delete(f"/users/{uid}")
    assert r.status_code == 204
    g = client.get(f"/users/{uid}")
    assert g.json()["is_active"] is False
