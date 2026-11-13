"""Error, accessibility-baseline, and OpenAPI contract checks."""

from fastapi.routing import APIRoute


def test_ct33_validation_and_auth_errors_are_not_success_responses(auth_client) -> None:
    client, _ = auth_client
    unauthenticated = client.get("/v1/auth/me")
    login = client.post(
        "/v1/auth/login",
        json={"email": "requester@example.test", "password": "requester-password"},
    )
    invalid_reservation = client.post(
        "/v1/reservations",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        json={"reason": "", "items": []},
    )

    assert unauthenticated.status_code == 401
    assert unauthenticated.json()["detail"] == "Credenciais inválidas ou sessão expirada."
    assert invalid_reservation.status_code == 422
    assert "detail" in invalid_reservation.json()


def test_ct35_openapi_operations_match_registered_api_routes(auth_client) -> None:
    client, _ = auth_client
    documented = client.get("/openapi.json").json()["paths"]
    expected = {
        (path, method.upper())
        for path, operations in documented.items()
        for method in operations
    }
    actual = {
        (route.path, method.upper())
        for route in client.app.routes
        if isinstance(route, APIRoute) and route.include_in_schema
        for method in (route.methods or set())
    }

    assert actual == expected
