"""Authentication and authorization checks for the public API."""

from app.models import User
from app.servicos.autenticacao import issue_access_token


def test_ct01_login_uses_generic_response_for_invalid_credentials(auth_client) -> None:
    client, _ = auth_client

    valid = client.post(
        "/v1/auth/login",
        json={"email": "admin@example.test", "password": "correct-password"},
    )
    invalid = client.post(
        "/v1/auth/login",
        json={"email": "admin@example.test", "password": "wrong-password"},
    )

    assert valid.status_code == 200
    assert valid.json()["access_token"]
    assert invalid.status_code == 401
    assert invalid.json()["detail"] == valid.json().get("detail", "Credenciais inválidas ou sessão expirada.")


def test_ct02_protected_route_rejects_missing_and_expired_tokens(auth_client) -> None:
    client, _ = auth_client
    missing = client.get("/v1/auth/me")
    assert missing.status_code == 401

    expired_token = issue_access_token("admin-1", now=0)
    expired = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert expired.status_code == 401
    assert expired.json()["detail"] == missing.json()["detail"]


def test_ct03_requester_cannot_call_admin_only_dependency(auth_client) -> None:
    client, session = auth_client
    login = client.post(
        "/v1/auth/login",
        json={"email": "requester@example.test", "password": "requester-password"},
    )
    initial_user_count = session.query(User).count()
    assert login.status_code == 200

    response = client.post(
        "/v1/admin/users",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        json={
            "name": "Unauthorized",
            "email": "unauthorized@example.test",
            "password": "password",
            "role": "ADMIN",
        },
    )

    assert response.status_code == 403
    assert session.query(User).count() == initial_user_count
