"""Project configuration and settings for the academic reservation system."""

import os
from dataclasses import dataclass, field

DEFAULT_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/alocasenac"


@dataclass(frozen=True)
class AppSettings:
    """Minimal settings container aligned with the PRD.

    The database URL is intentionally explicit so integration tests can target a
    real PostgreSQL instance without discounting the operational constraints in
    the NFRs.
    """

    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))
    app_name: str = "alocasenac"
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
