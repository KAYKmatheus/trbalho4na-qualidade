"""API and pages for the academic reservation system."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from app.db import get_db, init_db
from app.erros import ConflictError, ValidationError
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
      <head><title>AlocaSenac Dashboard</title></head>
      <body>
        <h1>AlocaSenac Dashboard</h1>
        <p>API de reservas acadêmicas com controle de conflitos e auditoria.</p>
        <ul>
          <li>Reservas</li>
          <li>Recursos</li>
          <li>API /v1</li>
        </ul>
      </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/v1/health")
def health() -> dict:
    return {"status": "ok", "service": "alocasenac"}


@app.post("/v1/reservations")
def create_reservation(payload: dict, session: Session = Depends(get_db)) -> JSONResponse:
    service = ReservationService(session)
    try:
        reservation = service.create_reservation(
            solicitante_id=payload["solicitante_id"],
            reason=payload["reason"],
            items=payload.get("items", []),
        )
    except (ConflictError, ValidationError) as exc:
        return JSONResponse(status_code=409 if isinstance(exc, ConflictError) else 422, content={"detail": str(exc)})

    return JSONResponse(
        status_code=201,
        content={
            "id": reservation.id,
            "solicitante_id": reservation.solicitante_id,
            "status": reservation.status,
            "items": [
                {
                    "resource_type": item.resource_type,
                    "resource_id": item.resource_id,
                    "start": item.start.isoformat(),
                    "end": item.end.isoformat(),
                    "status": item.status,
                }
                for item in reservation.items
            ],
        },
    )
