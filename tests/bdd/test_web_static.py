"""HTTP checks for the static web application."""

import re
from html.parser import HTMLParser
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


class StaticPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.language = None
        self.viewport = None
        self.input_ids = []
        self.label_targets = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "html":
            self.language = attributes.get("lang")
        elif tag == "meta" and attributes.get("name") == "viewport":
            self.viewport = attributes.get("content")
        elif tag == "input":
            self.input_ids.append(attributes.get("id"))
        elif tag == "label":
            self.label_targets.add(attributes.get("for"))


def test_static_pages_are_served_with_html_and_health_remains_available() -> None:
    client = TestClient(app)
    all_input_ids = []
    for page in ("index.html", "buscar.html", "reservar.html", "minhas.html"):
        response = client.get(f"/app/{page}")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

        parser = StaticPageParser()
        parser.feed(response.text)
        assert parser.language == "pt-BR"
        assert parser.viewport == "width=device-width, initial-scale=1"
        all_input_ids.extend(parser.input_ids)
        assert all(input_id and input_id in parser.label_targets for input_id in parser.input_ids)

    assert all_input_ids
    javascript = Path(__file__).resolve().parents[2] / "app" / "web" / "static" / "app.js"
    assert not re.search(r"(?:https?:)?//[A-Za-z0-9.-]+", javascript.read_text(encoding="utf-8"))

    health = client.get("/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"


def test_root_redirects_to_static_login_page() -> None:
    response = TestClient(app, follow_redirects=False).get("/")

    assert response.status_code == 307
    assert response.headers["location"] == "/app/index.html"
