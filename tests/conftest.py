"""Reusable in-memory database and authenticated API fixtures."""

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1 import app
from app.db import get_db, init_db
from app.models import Base, User
from app.servicos.autenticacao import hash_password


@pytest.fixture(scope="session")
def pg_engine() -> Generator[Engine, None, None]:
    database_url = os.getenv("DATABASE_URL")
    postgres_url = None
    if database_url:
        try:
            parsed_url = make_url(database_url)
        except ArgumentError:
            parsed_url = None
        if parsed_url is not None and parsed_url.get_backend_name() == "postgresql":
            if parsed_url.drivername == "postgresql":
                parsed_url = parsed_url.set(drivername="postgresql+psycopg")
            postgres_url = parsed_url.render_as_string(hide_password=False)

    container = None
    if postgres_url is None:
        from docker.errors import DockerException
        from testcontainers.postgres import PostgresContainer

        try:
            container = PostgresContainer("postgres:16", driver="psycopg")
        except DockerException as exc:
            pytest.skip(f"PostgreSQL integration tests require DATABASE_URL or Docker: {exc}")
        container.start()
        postgres_url = container.get_connection_url()

    engine = create_engine(postgres_url, future=True)
    try:
        init_db(engine)
        yield engine
    finally:
        engine.dispose()
        if container is not None:
            container.stop()


@pytest.fixture(scope="session")
def pg_session_factory(pg_engine: Engine) -> sessionmaker:
    return sessionmaker(bind=pg_engine, expire_on_commit=False)


@pytest.fixture
def clean_postgres_database(pg_engine: Engine) -> Generator[None, None, None]:
    def truncate() -> None:
        with pg_engine.begin() as connection:
            connection.execute(
                text(
                    "TRUNCATE audit_entries, reservation_items, reservations, "
                    "resource_blocks, resources, users, notifications "
                    "RESTART IDENTITY CASCADE"
                )
            )

    truncate()
    yield
    truncate()


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
