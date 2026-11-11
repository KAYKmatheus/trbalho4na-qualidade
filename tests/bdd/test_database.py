"""Database setup and migration parsing checks."""

from contextlib import contextmanager
from pathlib import Path
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
    target_engine = SimpleNamespace(dialect=SimpleNamespace(name="sqlite"))

    database._apply_sql_migrations(target_engine)


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

    target_engine = Engine()

    database._apply_sql_migrations(target_engine)

    assert len(executed) >= 7
    assert all(statement.strip() for statement in executed)


def test_migration_set_is_three_idempotent_subject_migrations() -> None:
    migration_dir = Path(__file__).resolve().parents[2] / "migrations"
    migration_names = sorted(path.name for path in migration_dir.glob("*.sql"))

    assert migration_names == [
        "001_initial_schema.sql",
        "002_exclusao_sobreposicao.sql",
        "003_auditoria_imutavel.sql",
    ]

    initial = (migration_dir / migration_names[0]).read_text(encoding="utf-8").upper()
    exclusion = (migration_dir / migration_names[1]).read_text(encoding="utf-8").upper()
    immutable = (migration_dir / migration_names[2]).read_text(encoding="utf-8").upper()

    assert "CREATE TABLE IF NOT EXISTS" in initial
    assert "ADD COLUMN IF NOT EXISTS" in initial
    assert "CREATE INDEX IF NOT EXISTS" in initial
    assert "CREATE EXTENSION IF NOT EXISTS BTREE_GIST" in exclusion
    assert "DROP CONSTRAINT IF EXISTS RESERVATION_ITEMS_NO_OVERLAP" in exclusion
    assert "EXCLUDE USING GIST" in exclusion
    assert 'TSTZRANGE(START, "END", \'[)\')' in exclusion
    assert "STATUS IN ('APROVADA', 'CONFIRMADA', 'EM_USO') AND RESOURCE_TYPE <> 'MATERIAL'" in exclusion
    assert immutable.count("ADD COLUMN IF NOT EXISTS") == 3
    assert immutable.count("DROP TRIGGER IF EXISTS") == 3
    assert immutable.count("CREATE TRIGGER") == 3


def test_init_db_creates_models_then_applies_migrations(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(Base.metadata, "create_all", lambda bind: calls.append(("create", bind)))
    monkeypatch.setattr(database, "_default_engine", "test-engine")
    monkeypatch.setattr(database, "_apply_sql_migrations", lambda bind: calls.append(("migrate", bind)))

    database.init_db()

    assert calls == [("create", "test-engine"), ("migrate", "test-engine")]


def test_init_db_uses_supplied_engine(monkeypatch) -> None:
    calls = []
    supplied_engine = object()
    monkeypatch.setattr(Base.metadata, "create_all", lambda bind: calls.append(("create", bind)))
    monkeypatch.setattr(database, "_apply_sql_migrations", lambda bind: calls.append(("migrate", bind)))

    database.init_db(supplied_engine)

    assert calls == [("create", supplied_engine), ("migrate", supplied_engine)]


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
