"""Database setup and migration parsing checks."""

from contextlib import contextmanager
from types import SimpleNamespace

import app.db as database
from app.models import Base


def test_split_sql_statements_preserves_quoted_semicolons() -> None:
    statements = database._split_sql_statements(
        "SELECT 'one; two'; SELECT 'escaped''; quote'; "
        'SELECT "column; name"; DO $tag$ BEGIN PERFORM 1; PERFORM 2; END $tag$;'
    )

    assert len(statements) == 4
    assert statements[0] == "SELECT 'one; two'"
    assert statements[1] == "SELECT 'escaped''; quote'"
    assert statements[2] == 'SELECT "column; name"'
    assert "PERFORM 1; PERFORM 2;" in statements[3]


def test_split_sql_statements_skips_empty_parts_and_keeps_tail() -> None:
    assert database._split_sql_statements(" ; SELECT 1; ; SELECT 2 ") == ["SELECT 1", "SELECT 2"]


def test_migrations_are_skipped_for_non_postgres(monkeypatch) -> None:
    monkeypatch.setattr(database, "engine", SimpleNamespace(dialect=SimpleNamespace(name="sqlite")))

    database._apply_sql_migrations()


def test_migrations_execute_each_postgres_statement(monkeypatch) -> None:
    executed = []

    class Connection:
        def execute(self, statement) -> None:
            executed.append(str(statement))

    class Engine:
        dialect = SimpleNamespace(name="postgresql")

        @contextmanager
        def begin(self):
            yield Connection()

    monkeypatch.setattr(database, "engine", Engine())

    database._apply_sql_migrations()

    assert len(executed) >= 7
    assert all(statement.strip() for statement in executed)


def test_init_db_creates_models_then_applies_migrations(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(Base.metadata, "create_all", lambda bind: calls.append(("create", bind)))
    monkeypatch.setattr(database, "engine", "test-engine")
    monkeypatch.setattr(database, "_apply_sql_migrations", lambda: calls.append(("migrate", None)))

    database.init_db()

    assert calls == [("create", "test-engine"), ("migrate", None)]


def test_get_db_closes_request_session(monkeypatch) -> None:
    class FakeSession:
        closed = False

        def close(self) -> None:
            self.closed = True

    session = FakeSession()
    monkeypatch.setattr(database, "SessionLocal", lambda: session)
    dependency = database.get_db()

    assert next(dependency) is session
    try:
        next(dependency)
    except StopIteration:
        pass

    assert session.closed
