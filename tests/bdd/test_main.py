"""Entrypoint behavior checks."""

import runpy
from importlib import reload
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parents[2]


def test_import_does_not_start_uvicorn(monkeypatch) -> None:
    import app.main as application

    calls = []
    monkeypatch.setattr(uvicorn, "run", lambda *args, **kwargs: calls.append((args, kwargs)))

    reload(application)

    assert calls == []


def test_module_entrypoint_starts_uvicorn(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(
        uvicorn,
        "run",
        lambda app, host, port: calls.append((app.title, host, port)),
    )

    runpy.run_path(str(ROOT / "app" / "main.py"), run_name="__main__")

    assert calls == [("AlocaSenac API", "0.0.0.0", 8000)]
