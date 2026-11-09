"""Real PostgreSQL concurrency tests for CT-19 and CT-20."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Barrier

import pytest
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session

from app_config import AppSettings
from domain_rules import ConflictError
from errors import ValidationError
from models import Material, ReservationItem
from services import ReservationService


@pytest.mark.integration
def test_ct19_postgres_exclusion_allows_only_one_overlapping_room(
    postgres_database_url: str,
) -> None:
    """CT-19: PostgreSQL deve arbitrar a disputa concorrente de sala."""
    service = ReservationService(AppSettings(database_url=postgres_database_url))
    barrier = Barrier(2)

    def request(user_id: str) -> bool:
        barrier.wait(timeout=30)
        try:
            service.create_reservation(
                solicitante_id=user_id,
                reason="Disputa simultanea de sala",
                items=[
                    {
                        "resource_type": "sala",
                        "resource_id": "room-ct19",
                        "start": datetime(2026, 2, 1, 9, tzinfo=timezone.utc),
                        "end": datetime(2026, 2, 1, 11, tzinfo=timezone.utc),
                    }
                ],
            )
            return True
        except ConflictError:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(request, ("ct19-user-a", "ct19-user-b")))

    assert sum(outcomes) == 1
    engine = create_engine(postgres_database_url, future=True)
    with Session(engine) as session:
        assert session.query(ReservationItem).filter_by(resource_id="room-ct19").count() == 1
    engine.dispose()


@pytest.mark.integration
def test_ct20_postgres_material_row_lock_enforces_stock_limit(
    postgres_database_url: str,
) -> None:
    """CT-20: estoque M deve aceitar no maximo M unidades concorrentes."""
    stock_limit = 3
    engine = create_engine(postgres_database_url, future=True)
    with Session(engine) as session, session.begin():
        session.add(
            Material(
                id="material-ct20",
                name="Projetor CT-20",
                quantity_total=stock_limit,
                active=True,
            )
        )

    service = ReservationService(AppSettings(database_url=postgres_database_url))
    barrier = Barrier(8)

    def request(user_id: str) -> bool:
        barrier.wait(timeout=30)
        try:
            service.create_reservation(
                solicitante_id=user_id,
                reason="Disputa simultanea de material",
                items=[
                    {
                        "resource_type": "material",
                        "resource_id": "material-ct20",
                        "start": datetime(2026, 2, 2, 9, tzinfo=timezone.utc),
                        "end": datetime(2026, 2, 2, 11, tzinfo=timezone.utc),
                        "quantity": 1,
                    }
                ],
            )
            return True
        except ConflictError:
            return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(request, (f"ct20-user-{index}" for index in range(8))))

    with Session(engine) as session:
        reserved = (
            session.query(func.coalesce(func.sum(ReservationItem.quantity), 0))
            .filter_by(resource_id="material-ct20")
            .scalar()
        )
        assert sum(outcomes) == stock_limit
        assert reserved == stock_limit
    engine.dispose()


@pytest.mark.integration
@pytest.mark.parametrize(
    "item",
    [
        {"resource_type": "sala", "resource_id": "room-invalid"},
        {
            "resource_type": "sala",
            "resource_id": "room-invalid",
            "start": datetime(2026, 2, 3, 10, tzinfo=timezone.utc),
            "end": datetime(2026, 2, 3, 9, tzinfo=timezone.utc),
        },
        {
            "resource_type": "material",
            "resource_id": "material-invalid",
            "start": datetime(2026, 2, 3, 9, tzinfo=timezone.utc),
            "end": datetime(2026, 2, 3, 10, tzinfo=timezone.utc),
            "quantity": 0,
        },
        {
            "resource_type": "material",
            "resource_id": "missing-material",
            "start": datetime(2026, 2, 3, 9, tzinfo=timezone.utc),
            "end": datetime(2026, 2, 3, 10, tzinfo=timezone.utc),
            "quantity": 1,
        },
        {
            "resource_type": "sala",
            "resource_id": "room-invalid",
            "start": datetime(2026, 2, 3, 9, tzinfo=timezone.utc),
            "end": datetime(2026, 2, 3, 10, tzinfo=timezone.utc),
            "quantity": 2,
        },
    ],
)
def test_postgres_rejects_invalid_reservation_item(
    postgres_database_url: str,
    item: dict,
) -> None:
    service = ReservationService(AppSettings(database_url=postgres_database_url))

    with pytest.raises(ValidationError):
        service.create_reservation(
            solicitante_id="ct-validation-user",
            reason="Validacao de item",
            items=[item],
        )


@pytest.mark.integration
def test_sql_helper_executes_query_against_postgres(postgres_database_url: str) -> None:
    import models

    result = models.execute_sql("SELECT 1", postgres_database_url)

    assert result.returns_rows