"""Project configuration and settings for the academic reservation system."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AppSettings:
    """Minimal settings container aligned with the PRD.

    The database URL is intentionally explicit so integration tests can target a
    real PostgreSQL instance without discounting the operational constraints in
    the NFRs.
    """

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/alocasenac"
    app_name: str = "alocasenac"
