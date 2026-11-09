"""Shared PostgreSQL Testcontainers fixtures for integration tests."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from testcontainers.postgres import PostgresContainer

from app_config import AppSettings
import models


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer(
        "postgres:16-alpine",
        driver="psycopg",
        username="postgres",
        password="postgres",
        dbname="alocasenac_test",
    ) as container:
        yield container


@pytest.fixture
def postgres_database_url(postgres_container) -> str:
    database_url = postgres_container.get_connection_url()
    engine = create_engine(database_url, future=True)
    models.Base.metadata.drop_all(engine)
    models.init_db(database_url)
    models.configure_database(AppSettings(database_url=database_url))

    yield database_url

    models.Base.metadata.drop_all(engine)
    engine.dispose()
    if models.Engine is not None:
        models.Engine.dispose()