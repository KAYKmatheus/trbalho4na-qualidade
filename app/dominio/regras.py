"""Pure business rules for reservation integrity.

These rules are intentionally free of persistence concerns and map directly to the
PRD requirements: FR-06, FR-07, RN02, RN03, RN04 and the material availability
corner cases in CT-15, CT-18 and CT-20.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from app.erros import ValidationError


class StatusReserva(str, Enum):
    SOLICITADA = "SOLICITADA"
    PENDENTE = "PENDENTE"
    APROVADA = "APROVADA"
    CONFIRMADA = "CONFIRMADA"
    EM_USO = "EM_USO"
    CONCLUIDA = "CONCLUIDA"
    REJEITADA = "REJEITADA"
    CANCELADA = "CANCELADA"
    NAO_COMPARECEU = "NAO_COMPARECEU"


ACTIVE_RESERVATION_STATUSES = (
    StatusReserva.APROVADA.value,
    StatusReserva.CONFIRMADA.value,
    StatusReserva.EM_USO.value,
)


_RESERVATION_TRANSITIONS = {
    StatusReserva.SOLICITADA: {StatusReserva.PENDENTE, StatusReserva.CANCELADA},
    StatusReserva.PENDENTE: {
        StatusReserva.APROVADA,
        StatusReserva.REJEITADA,
        StatusReserva.CANCELADA,
    },
    StatusReserva.APROVADA: {
        StatusReserva.CONFIRMADA,
        StatusReserva.CANCELADA,
        StatusReserva.NAO_COMPARECEU,
    },
    StatusReserva.CONFIRMADA: {
        StatusReserva.EM_USO,
        StatusReserva.CANCELADA,
        StatusReserva.NAO_COMPARECEU,
    },
    StatusReserva.EM_USO: {StatusReserva.CONCLUIDA},
    StatusReserva.CONCLUIDA: set(),
    StatusReserva.REJEITADA: set(),
    StatusReserva.CANCELADA: set(),
    StatusReserva.NAO_COMPARECEU: set(),
}


def transition_reservation_status(current: str | StatusReserva, target: str | StatusReserva) -> StatusReserva:
    """Validate and return a reservation status transition."""
    try:
        current_status = StatusReserva(current)
        target_status = StatusReserva(target)
    except ValueError as exc:
        raise ValidationError("Estado de reserva inválido.") from exc
    if target_status not in _RESERVATION_TRANSITIONS[current_status]:
        raise ValidationError(f"Transição de {current_status.value} para {target_status.value} não permitida.")
    return target_status


def _require_timezone_aware(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValidationError(f"{field_name} deve conter informação de fuso horário.")
    return value


def is_overlapping_interval(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
    """Return True when two intervals overlap using the documented open-ended rule."""
    start_a = _require_timezone_aware(start_a, "start_a")
    end_a = _require_timezone_aware(end_a, "end_a")
    start_b = _require_timezone_aware(start_b, "start_b")
    end_b = _require_timezone_aware(end_b, "end_b")

    if start_a >= end_a or start_b >= end_b:
        raise ValidationError("Intervalos devem ter início antes do fim.")
    return max(start_a, start_b) < min(end_a, end_b)


def material_stock_available(*, available: int, reserved: int, requested: int) -> bool:
    """Check whether a material request can still be accommodated.

    The function is intentionally pure: it returns True only when the requested
    units can be respected with the current committed reserve. The service layer
    converts False to a domain ConflictError for the API and transaction boundary.
    """
    if available < 0:
        raise ValidationError("Estoque disponível não pode ser negativo.")
    if reserved < 0:
        raise ValidationError("Quantidade reservada não pode ser negativa.")
    if requested <= 0:
        raise ValidationError("Quantidade solicitada deve ser maior que zero.")

    net_available = max(0, available - reserved)
    return requested <= net_available
