"""Persistence models and the transactional boundary for the reservation system."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    solicitante_id = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    status = Column(String, nullable=False, default="PENDENTE")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    items = relationship("ReservationItem", back_populates="reservation", cascade="all, delete-orphan")


class ReservationItem(Base):
    __tablename__ = "reservation_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    reservation_id = Column(String, ForeignKey("reservations.id"), nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=False)
    start = Column(DateTime(timezone=True), nullable=False)
    end = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, nullable=False, default="PENDENTE")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    reservation = relationship("Reservation", back_populates="items")


class AuditEntry(Base):
    __tablename__ = "audit_entries"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    payload = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
