"""PostgreSQL integration tests for persistence and concurrency."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import AppSettings
from app.db import init_db
from app.erros import ConflictError
from app.models import Base
from app.servicos.reservas import ReservationService


@pytest.fixture(scope="module", autouse=True)
def initialize_postgres_schema() -> None:
    init_db()


@pytest.mark.integration
@pytest.mark.parametrize(
    "resource_type, resource_id, start, end",
    [
        ("sala", "room-7", "2026-01-12T08:00:00Z", "2026-01-12T10:00:00Z"),
        ("professor", "teacher-7", "2026-01-12T08:00:00Z", "2026-01-12T10:00:00Z"),
    ],
)
def test_postgres_real_database_accepts_integration_write(
    resource_type: str, resource_id: str, start: str, end: str
) -> None:
    """Verifica acesso e gravação no PostgreSQL de integração."""
    resource_id = f"{resource_id}-{uuid4().hex}"
    engine = create_engine(AppSettings().database_url)
    try:
        with engine.begin() as conn:
            conn.execute(text("SELECT 1"))
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS integration_probe "
                    "(resource_type TEXT, resource_id TEXT, start_ts TIMESTAMPTZ, end_ts TIMESTAMPTZ)"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO integration_probe "
                    "(resource_type, resource_id, start_ts, end_ts) "
                    "VALUES (:resource_type, :resource_id, :start, :end)"
                ),
                {
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "start": start,
                    "end": end,
                },
            )
            row = conn.execute(
                text(
                    "SELECT COUNT(*) FROM integration_probe "
                    "WHERE resource_type = :resource_type AND resource_id = :resource_id"
                ),
                {"resource_type": resource_type, "resource_id": resource_id},
            ).scalar_one()
            assert row == 1
    finally:
        engine.dispose()


@pytest.mark.integration
@pytest.mark.concorrencia
def test_concurrent_room_requests_only_one_reservation_succeeds() -> None:
    """Verifica FR-07, RN04, NFR-03, CT-19."""
    engine = create_engine(AppSettings().database_url)
    Base.metadata.create_all(engine)
    integration_session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    resource_id = f"room-concurrent-{uuid4().hex}"

    def attempt(user_id: str):
        with integration_session_factory() as session:
            try:
                return ReservationService(session).create_reservation(
                    solicitante_id=user_id,
                    reason="Reserva concorrente",
                    items=[
                        {
                            "resource_type": "sala",
                            "resource_id": resource_id,
                            "start": datetime(2026, 2, 1, 9, 0, tzinfo=timezone.utc),
                            "end": datetime(2026, 2, 1, 11, 0, tzinfo=timezone.utc),
                        }
                    ],
                )
            except ConflictError:
                return None

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, ["user-a", "user-b"]))
        assert sum(result is not None for result in results) == 1
    finally:
        engine.dispose()
