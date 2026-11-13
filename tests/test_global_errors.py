"""Tests for application-wide unexpected error handling."""

from fastapi.testclient import TestClient

from app.main import app


def test_unexpected_error_returns_generic_json_without_internal_details() -> None:
    def fail_with_internal_error() -> None:
        raise RuntimeError("segredo-interno")

    path = "/_test/unexpected-error"
    app.add_api_route(path, fail_with_internal_error, methods=["GET"])
    try:
        response = TestClient(app, raise_server_exceptions=False).get(path)
    finally:
        app.router.routes = [route for route in app.router.routes if getattr(route, "path", None) != path]

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"detail": "Erro interno do servidor."}
    assert "segredo-interno" not in response.text
    assert "Traceback" not in response.text
