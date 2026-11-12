"""HTTP checks for the static web application."""

from fastapi.testclient import TestClient

from app.main import app


def test_static_pages_are_served_with_html_and_health_remains_available() -> None:
    client = TestClient(app)
    for page in ("index.html", "buscar.html", "reservar.html", "minhas.html"):
        response = client.get(f"/app/{page}")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

    health = client.get("/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"


def test_root_redirects_to_static_login_page() -> None:
    response = TestClient(app, follow_redirects=False).get("/")

    assert response.status_code == 307
    assert response.headers["location"] == "/app/index.html"
