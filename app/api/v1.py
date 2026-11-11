"""API and pages for the academic reservation system."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user, require_roles
from app.api.schemas import (
    ApprovalCreate,
    LoginRequest,
    LoginResponse,
    MaintenanceCreate,
    MaterialBalanceRead,
    MaterialMovementCreate,
    ReservationCreate,
    ReservationRead,
    ReservationStatusUpdate,
    ReservationUpdate,
    ResourceAvailabilityRead,
    ResourceCreate,
    ResourceRead,
    ResourceScopeCreate,
    ResourceUpdate,
    UserCreate,
    UserRead,
    UtilizationReportRead,
)
from app.db import get_db, init_db
from app.erros import ConflictError, PermissaoNegadaError, ValidationError
from app.servicos.aprovacoes import ApprovalService
from app.servicos.autenticacao import AuthenticationService
from app.servicos.disponibilidade import AvailabilityService
from app.servicos.manutencao import MaintenanceService
from app.servicos.materiais import MaterialService
from app.servicos.recursos import ResourceService
from app.servicos.relatorios import ReportService
from app.servicos.reservas import ReservationService


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(title="AlocaSenac API", version="0.1.0", lifespan=lifespan)


@app.get("/")
def home_page() -> HTMLResponse:
    """Return a simple dashboard page for the reservation backbone."""
    html = """
    <html>
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>AlocaSenac Dashboard</title>
        <style>
          * { box-sizing: border-box; }
          body { margin: 0; min-width: 0; font-family: Arial, sans-serif; overflow-x: hidden; }
          main { width: 100%; max-width: 920px; margin: 0 auto; padding: 2rem 1rem; }
          nav { display: flex; flex-wrap: wrap; gap: 1rem; }
          nav a { color: #075985; }
          nav a:focus-visible { outline: 3px solid #b45309; outline-offset: 3px; }
          ul { padding-left: 1.2rem; overflow-wrap: anywhere; }
        </style>
      </head>
      <body>
        <main>
          <h1>AlocaSenac Dashboard</h1>
          <p>API de reservas acadêmicas com controle de conflitos e auditoria.</p>
          <nav aria-label="Navegação principal">
            <a href="/docs">Documentação da API</a>
            <a href="/v1/health">Status do serviço</a>
          </nav>
          <ul>
            <li>Reservas</li>
            <li>Recursos</li>
            <li>API /v1</li>
          </ul>
        </main>
      </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/v1/health")
def health() -> dict:
    return {"status": "ok", "service": "alocasenac"}


@app.post("/v1/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, session: Session = Depends(get_db)) -> LoginResponse:
    authenticated = AuthenticationService(session).authenticate(payload.email, payload.password)
    if authenticated is None:
        raise HTTPException(
            status_code=401,
            detail="Credenciais inválidas ou sessão expirada.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    _, token = authenticated
    return LoginResponse(access_token=token)


@app.get("/v1/auth/me")
def current_user(user: CurrentUser = Depends(get_current_user)) -> dict[str, str]:
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}


@app.post("/v1/admin/users", response_model=UserRead, status_code=201)
def create_user(
    payload: UserCreate,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(require_roles("ADMIN")),
) -> UserRead:
    try:
        user = AuthenticationService(session).create_user(
            name=payload.name,
            email=payload.email,
            password=payload.password,
            role=payload.role,
        )
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return UserRead.model_validate(user, from_attributes=True)


@app.post("/v1/admin/resources", response_model=ResourceRead, status_code=201)
def create_resource(
    payload: ResourceCreate,
    session: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles("ADMIN")),
) -> ResourceRead:
    try:
        resource = ResourceService(session).create(
            actor_id=user.id,
            values=payload.model_dump(exclude_none=True),
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ResourceRead.model_validate(resource, from_attributes=True)


@app.get("/v1/admin/resources", response_model=list[ResourceRead])
def list_resources(
    resource_type: str | None = None,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(require_roles("ADMIN")),
) -> list[ResourceRead]:
    resources = ResourceService(session).list(resource_type=resource_type)
    return [ResourceRead.model_validate(resource, from_attributes=True) for resource in resources]


@app.get("/v1/admin/resources/{resource_id}", response_model=ResourceRead)
def get_resource(
    resource_id: str,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(require_roles("ADMIN")),
) -> ResourceRead:
    resource = ResourceService(session).get(resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail="Recurso não encontrado.")
    return ResourceRead.model_validate(resource, from_attributes=True)


@app.patch("/v1/admin/resources/{resource_id}", response_model=ResourceRead)
def update_resource(
    resource_id: str,
    payload: ResourceUpdate,
    session: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles("ADMIN")),
) -> ResourceRead:
    try:
        resource = ResourceService(session).update(
            actor_id=user.id,
            resource_id=resource_id,
            changes=payload.model_dump(exclude_unset=True),
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if resource is None:
        raise HTTPException(status_code=404, detail="Recurso não encontrado.")
    return ResourceRead.model_validate(resource, from_attributes=True)


@app.post("/v1/admin/responsaveis/{responsible_id}/recursos", status_code=201)
def assign_resource_scope(
    responsible_id: str,
    payload: ResourceScopeCreate,
    session: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles("ADMIN")),
) -> dict[str, str]:
    try:
        scope = ResourceService(session).assign_scope(
            actor_id=user.id,
            responsible_id=responsible_id,
            resource_id=payload.resource_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissaoNegadaError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"id": scope.id, "responsible_id": scope.responsible_id, "resource_id": scope.resource_id}


@app.delete("/v1/admin/responsaveis/{responsible_id}/recursos/{resource_id}", status_code=204)
def remove_resource_scope(
    responsible_id: str,
    resource_id: str,
    session: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles("ADMIN")),
) -> Response:
    removed = ResourceService(session).remove_scope(
        actor_id=user.id,
        responsible_id=responsible_id,
        resource_id=resource_id,
    )
    if not removed:
        raise HTTPException(status_code=404, detail="Recurso não encontrado no escopo do Responsável.")
    return Response(status_code=204)


@app.post("/v1/admin/resources/{resource_id}/maintenance", status_code=201)
def create_maintenance(
    resource_id: str,
    payload: MaintenanceCreate,
    session: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles("ADMIN")),
) -> dict[str, str]:
    try:
        block = MaintenanceService(session).create_block(
            resource_id=resource_id,
            actor_id=user.id,
            start=payload.start,
            end=payload.end,
            reason=payload.reason,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "id": block.id,
        "resource_id": block.resource_id,
        "start": block.start.isoformat(),
        "end": block.end.isoformat(),
        "status": block.status,
    }


@app.get("/v1/resources/search", response_model=list[ResourceAvailabilityRead])
def search_resources(
    start: datetime,
    end: datetime,
    resource_type: str | None = None,
    capacity: int | None = None,
    location: str | None = None,
    competency: str | None = None,
    quantity: int = 1,
    session: Session = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> list[ResourceAvailabilityRead]:
    try:
        resources = AvailabilityService(session).search(
            start=start,
            end=end,
            resource_type=resource_type,
            capacity=capacity,
            location=location,
            competency=competency,
            quantity=quantity,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return [ResourceAvailabilityRead.model_validate(resource) for resource in resources]


@app.post("/v1/reservations/items/{item_id}/decision", response_model=ReservationRead)
def decide_reservation_item(
    item_id: str,
    payload: ApprovalCreate,
    session: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles("RESPONSAVEL")),
) -> ReservationRead:
    try:
        reservation = ApprovalService(session).decide(
            item_id=item_id,
            responsible_id=user.id,
            decision_type=payload.decision_type,
            decision=payload.decision,
            justification=payload.justification,
        )
    except PermissaoNegadaError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if reservation is None:
        raise HTTPException(status_code=404, detail="Item da reserva não encontrado.")
    return ReservationRead.model_validate(reservation, from_attributes=True)


@app.post("/v1/reservations/items/{item_id}/movements", status_code=201)
def record_material_movement(
    item_id: str,
    payload: MaterialMovementCreate,
    session: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles("RESPONSAVEL")),
) -> dict[str, str | int]:
    try:
        movement = MaterialService(session).record_movement(
            item_id=item_id,
            responsible_id=user.id,
            movement_type=payload.movement_type,
            quantity=payload.quantity,
            observation=payload.observation,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissaoNegadaError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "id": movement.id,
        "item_id": movement.reservation_item_id,
        "movement_type": movement.movement_type,
        "quantity": movement.quantity,
    }


@app.get("/v1/reservations/items/{item_id}/material-balance", response_model=MaterialBalanceRead)
def get_material_balance(
    item_id: str,
    session: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles("RESPONSAVEL")),
) -> MaterialBalanceRead:
    try:
        balance = MaterialService(session).balance(item_id=item_id, responsible_id=user.id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissaoNegadaError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return MaterialBalanceRead(**balance)


@app.get("/v1/admin/reports", response_model=UtilizationReportRead)
def get_utilization_report(
    start: datetime,
    end: datetime,
    session: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles("ADMIN", "RESPONSAVEL")),
) -> UtilizationReportRead:
    try:
        report = ReportService(session).generate(
            start=start,
            end=end,
            user_id=user.id,
            role=user.role,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return UtilizationReportRead.model_validate(report)


@app.post("/v1/reservations", response_model=ReservationRead, status_code=201)
def create_reservation(
    payload: ReservationCreate,
    session: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> ReservationRead:
    service = ReservationService(session)
    try:
        reservation = service.create_reservation(
            solicitante_id=user.id,
            reason=payload.reason,
            items=[item.model_dump(mode="python") for item in payload.items],
        )
    except (ConflictError, ValidationError) as exc:
        status_code = 409 if isinstance(exc, ConflictError) else 422
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    except PermissaoNegadaError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except PydanticValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    return ReservationRead.model_validate(reservation, from_attributes=True)


@app.patch("/v1/reservations/{reservation_id}", response_model=ReservationRead)
def update_reservation(
    reservation_id: str,
    payload: ReservationUpdate,
    session: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> ReservationRead:
    try:
        reservation = ReservationService(session).update_reservation(
            reservation_id=reservation_id,
            actor_id=user.id,
            reason=payload.reason,
            items=[item.model_dump(mode="python") for item in payload.items] if payload.items is not None else None,
        )
    except PermissaoNegadaError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reserva não encontrada.")
    return ReservationRead.model_validate(reservation, from_attributes=True)


@app.delete("/v1/reservations/{reservation_id}", response_model=ReservationRead)
def cancel_reservation(
    reservation_id: str,
    session: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> ReservationRead:
    try:
        reservation = ReservationService(session).cancel_reservation(
            reservation_id=reservation_id,
            actor_id=user.id,
        )
    except PermissaoNegadaError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reserva não encontrada.")
    return ReservationRead.model_validate(reservation, from_attributes=True)


@app.patch("/v1/reservations/{reservation_id}/status", response_model=ReservationRead)
def transition_reservation_status(
    reservation_id: str,
    payload: ReservationStatusUpdate,
    session: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles("ADMIN", "RESPONSAVEL")),
) -> ReservationRead:
    try:
        reservation = ReservationService(session).transition_reservation(
            reservation_id=reservation_id,
            target_status=payload.status.value,
            actor_id=user.id,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reserva não encontrada.")
    return ReservationRead.model_validate(reservation, from_attributes=True)
