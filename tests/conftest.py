"""Reusable in-memory database and authenticated API fixtures."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1 import app
from app.db import get_db
from app.models import Base, User
from app.servicos.autenticacao import hash_password


@pytest.fixture
def auth_client(monkeypatch: pytest.MonkeyPatch) -> Generator[tuple[TestClient, Session], None, None]:
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-key-with-enough-entropy")
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = test_session_factory()
    session.add_all(
        [
            User(
                id="admin-1",
                name="Admin",
                email="admin@example.test",
                password_hash=hash_password("correct-password"),
                role="ADMIN",
                active=True,
            ),
            User(
                id="responsible-1",
                name="Responsible",
                email="responsible@example.test",
                password_hash=hash_password("responsible-password"),
                role="RESPONSAVEL",
                active=True,
            ),
            User(
                id="requester-1",
                name="Requester",
                email="requester@example.test",
                password_hash=hash_password("requester-password"),
                role="SOLICITANTE",
                active=True,
            ),
        ]
    )
    session.commit()

    def override_get_db() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app), session
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()
        engine.dispose()
