"""PostgreSQL integration tests for database initialization."""

import pytest

from app.db import init_db


@pytest.mark.integration
def test_init_db_can_apply_migrations_twice() -> None:
    """Verifica que o esquema e as migrações podem ser inicializados repetidamente."""
    init_db()
    init_db()
