"""Unit tests for pure reservation domain rules."""

import builtins
from datetime import datetime, timezone

import pytest

from app import erros
from app.dominio.regras import (
    StatusReserva,
    is_overlapping_interval,
    material_stock_available,
    transition_reservation_status,
)
from app.erros import PermissaoNegadaError, ValidationError


def test_permission_denied_exception_does_not_shadow_builtin() -> None:
    assert erros.PermissaoNegadaError is PermissaoNegadaError
    assert not hasattr(erros, "PermissionError")
    assert builtins.PermissionError is PermissionError


def test_interval_overlap_rule_detects_conflict() -> None:
    """Verifica FR-06, RN02, CT-15."""
    assert is_overlapping_interval(
        datetime(2026, 1, 10, 9, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 10, 11, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc),
    )
    assert not is_overlapping_interval(
        datetime(2026, 1, 10, 9, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 10, 11, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 10, 11, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc),
    )


def test_material_stock_is_rejected_when_exceeded() -> None:
    """Verifica FR-06, RN02, CT-18 e CT-20."""
    assert material_stock_available(available=5, reserved=3, requested=2) is True
    assert material_stock_available(available=5, reserved=3, requested=3) is False
    assert material_stock_available(available=4, reserved=3, requested=2) is False


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (StatusReserva.SOLICITADA, StatusReserva.PENDENTE),
        (StatusReserva.PENDENTE, StatusReserva.APROVADA),
        (StatusReserva.APROVADA, StatusReserva.CONFIRMADA),
        (StatusReserva.CONFIRMADA, StatusReserva.EM_USO),
        (StatusReserva.EM_USO, StatusReserva.CONCLUIDA),
    ],
)
def test_reservation_status_transition_follows_the_confirmed_lifecycle(current, target) -> None:
    assert transition_reservation_status(current, target) is target


def test_final_reservation_status_cannot_transition() -> None:
    with pytest.raises(ValidationError):
        transition_reservation_status(StatusReserva.CANCELADA, StatusReserva.PENDENTE)


@pytest.mark.parametrize(
    ("start_a", "end_a", "start_b", "end_b"),
    [
        (9, 8, 10, 11),
        (9, 10, 11, 10),
    ],
)
def test_invalid_interval_is_rejected(start_a, end_a, start_b, end_b) -> None:
    intervals = [
        datetime(2026, 1, 10, hour, tzinfo=timezone.utc)
        for hour in (start_a, end_a, start_b, end_b)
    ]

    with pytest.raises(ValidationError, match="Intervalos devem ter início antes do fim."):
        is_overlapping_interval(*intervals)
