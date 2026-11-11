"""Pydantic schemas for the reservation API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.dominio.regras import StatusReserva


class LoginRequest(BaseModel):
    """Credentials submitted to the login endpoint."""

    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Signed bearer token returned after successful login."""

    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    """Data required for an administrator to create an account."""

    name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    role: str = Field(..., pattern="^(ADMIN|RESPONSAVEL|SOLICITANTE)$")


class UserRead(BaseModel):
    """Public account fields; password hashes are never serialized."""

    id: str
    name: str
    email: str
    role: str
    active: bool


class ResourceCreate(BaseModel):
    """Fields shared by sala, professor, and material resources."""

    resource_type: Literal["sala", "professor", "material"]
    name: str = Field(..., min_length=1)
    category: str | None = None
    capacity: int | None = Field(default=None, gt=0)
    location: str | None = None
    competencies: list[str] | None = None
    quantity_total: int | None = Field(default=None, ge=0)
    restricted: bool = False


class ResourceUpdate(BaseModel):
    """Editable fields for an existing resource."""

    name: str | None = Field(default=None, min_length=1)
    category: str | None = None
    capacity: int | None = Field(default=None, gt=0)
    location: str | None = None
    competencies: list[str] | None = None
    quantity_total: int | None = Field(default=None, ge=0)
    restricted: bool | None = None
    active: bool | None = None


class ResourceRead(BaseModel):
    """Resource data exposed by the administrative API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    resource_type: str
    name: str
    category: str | None
    capacity: int | None
    location: str | None
    competencies: list[str] | None
    quantity_total: int | None
    restricted: bool
    active: bool


class ResourceAvailabilityRead(ResourceRead):
    """Resource data plus the number of available material units."""

    available_quantity: int | None = None


class ResourceScopeCreate(BaseModel):
    """Resource assigned to a responsible user's decision scope."""

    resource_id: str = Field(..., min_length=1)


class MaintenanceCreate(BaseModel):
    """Maintenance interval registered for one resource."""

    start: datetime
    end: datetime
    reason: str = Field(..., min_length=1)

    @field_validator("start", "end")
    @classmethod
    def ensure_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Data deve incluir fuso horário.")
        return value


class MaterialMovementCreate(BaseModel):
    """Material withdrawal or return event."""

    movement_type: Literal["RETIRADA", "DEVOLUCAO"]
    quantity: int = Field(..., gt=0)
    observation: str | None = None


class MaterialBalanceRead(BaseModel):
    """Current withdrawn, returned, and outstanding quantities."""

    withdrawn: int
    returned: int
    pending: int


class ReportResourceRead(BaseModel):
    """Utilization statistics for one resource."""

    resource_type: str
    resource_id: str
    resource_name: str
    reservation_count: int
    allocated_hours: float


class UtilizationReportRead(BaseModel):
    """Utilization, teaching load, and avoided-conflict totals."""

    period_start: datetime
    period_end: datetime
    utilization: list[ReportResourceRead]
    teaching_hours: float
    conflicts_avoided: int


class ReservationItemInput(BaseModel):
    """Input payload for one reservation item."""

    model_config = ConfigDict(extra="allow")

    resource_type: str = Field(..., min_length=1)
    resource_id: str = Field(..., min_length=1)
    start: datetime
    end: datetime
    quantity: int = Field(default=1, gt=0)

    @field_validator("start", "end")
    @classmethod
    def ensure_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Data deve incluir fuso horário.")
        return value


class ReservationCreate(BaseModel):
    """API payload for creating a reservation."""

    solicitante_id: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    items: list[ReservationItemInput] = Field(..., min_length=1)


class ReservationUpdate(BaseModel):
    """Fields that a requester may change before a reservation is decided."""

    reason: str | None = Field(default=None, min_length=1)
    items: list[ReservationItemInput] | None = Field(default=None, min_length=1)


class ReservationStatusUpdate(BaseModel):
    """Target state for an authorized reservation transition."""

    status: StatusReserva


class ApprovalCreate(BaseModel):
    """Approval or teacher-validation decision for one reservation item."""

    decision_type: Literal["RECURSO_RESTRITO", "VALIDACAO_DOCENTE"]
    decision: Literal["APROVADA", "REJEITADA"]
    justification: str = Field(..., min_length=1)


class ReservationItemRead(BaseModel):
    """Single reservation item as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    resource_type: str
    resource_id: str
    start: datetime
    end: datetime
    status: str


class ReservationRead(BaseModel):
    """Reservation payload returned after creation."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    solicitante_id: str
    status: str
    items: list[ReservationItemRead]


class ErrorResponse(BaseModel):
    """Standard error body for API failures."""

    detail: str
