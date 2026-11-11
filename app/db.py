"""Shared database engine, session factory, and FastAPI session dependency."""

import re
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import AppSettings

settings = AppSettings()
engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


def _apply_sql_migrations() -> None:
    """Apply incremental SQL migrations in the project order when the engine targets PostgreSQL."""
    if engine.dialect.name != "postgresql":
        return

    migration_dir = Path(__file__).resolve().parents[1] / "migrations"
    for migration_file in sorted(migration_dir.glob("*.sql")):
        sql_text = migration_file.read_text(encoding="utf-8")
        statements = _split_sql_statements(sql_text)
        with engine.begin() as conn:
            for statement in statements:
                conn.execute(text(statement))


def _split_sql_statements(sql_text: str) -> list[str]:
    """Split SQL at semicolons outside quoted strings and dollar-quoted bodies."""
    statements: list[str] = []
    current: list[str] = []
    single_quoted = False
    double_quoted = False
    dollar_quote: str | None = None
    index = 0

    while index < len(sql_text):
        if dollar_quote:
            if sql_text.startswith(dollar_quote, index):
                current.append(dollar_quote)
                index += len(dollar_quote)
                dollar_quote = None
                continue
        elif sql_text[index] == "$":
            match = re.match(r"\$[A-Za-z_0-9]*\$", sql_text[index:])
            if match:
                dollar_quote = match.group()
                current.append(dollar_quote)
                index += len(dollar_quote)
                continue

        char = sql_text[index]
        if not dollar_quote:
            if char == "'" and not double_quoted:
                if single_quoted and index + 1 < len(sql_text) and sql_text[index + 1] == "'":
                    current.extend(("'", "'"))
                    index += 2
                    continue
                single_quoted = not single_quoted
            elif char == '"' and not single_quoted:
                double_quoted = not double_quoted
            elif char == ";" and not single_quoted and not double_quoted:
                statement = "".join(current).strip()
                if statement:
                    statements.append(statement)
                current.clear()
                index += 1
                continue
        current.append(char)
        index += 1

    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


def init_db() -> None:
    """Create the application schema and apply ordered SQL migrations."""
    from app.models import Base

    Base.metadata.create_all(bind=engine)
    _apply_sql_migrations()


def get_db() -> Generator[Session, None, None]:
    """Yield a request-scoped database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
