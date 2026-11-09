"""Project configuration and settings for the academic reservation system."""

from dataclasses import dataclass, field
import os


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://localhost:5432/alocasenac",
    )


@dataclass(frozen=True)
class AppSettings:
    """Minimal settings container aligned with the PRD.

    The database URL is intentionally explicit so integration tests can target a
    real PostgreSQL instance without discounting the operational constraints in
    the NFRs.
    """

    database_url: str = field(default_factory=_database_url)
    app_name: str = field(default_factory=lambda: os.environ.get("APP_NAME", "alocasenac"))
