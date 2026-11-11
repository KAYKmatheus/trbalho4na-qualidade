"""Persistence models and the transactional boundary for the reservation system."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
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


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class Resource(Base):
    __tablename__ = "resources"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    resource_type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    capacity = Column(Integer, nullable=True)
    location = Column(String, nullable=True)
    competencies = Column(JSON, nullable=True)
    quantity_total = Column(Integer, nullable=True)
    restricted = Column(Boolean, nullable=False, default=False)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ResourceScope(Base):
    __tablename__ = "resource_scopes"
    __table_args__ = (UniqueConstraint("responsible_id", "resource_id", name="uq_responsible_resource_scope"),)

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    responsible_id = Column(String, ForeignKey("users.id"), nullable=False)
    resource_id = Column(String, ForeignKey("resources.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class ResourceBlock(Base):
    __tablename__ = "resource_blocks"
    __table_args__ = (CheckConstraint('start < "end"', name="ck_resource_block_period"),)

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    resource_id = Column(String, ForeignKey("resources.id"), nullable=False)
    start = Column(DateTime(timezone=True), nullable=False)
    end = Column(DateTime(timezone=True), nullable=False)
    reason = Column(String, nullable=False)
    status = Column(String, nullable=False, default="ATIVO")
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    reservation_item_id = Column(String, ForeignKey("reservation_items.id"), nullable=False)
    responsible_id = Column(String, ForeignKey("users.id"), nullable=False)
    decision_type = Column(String, nullable=False)
    decision = Column(String, nullable=False)
    justification = Column(String, nullable=False)
    decided_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class MaterialMovement(Base):
    __tablename__ = "material_movements"
    __table_args__ = (
        CheckConstraint("movement_type IN ('RETIRADA', 'DEVOLUCAO')", name="ck_material_movement_type"),
        CheckConstraint("quantity > 0", name="ck_material_movement_quantity"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    reservation_item_id = Column(String, ForeignKey("reservation_items.id"), nullable=False)
    responsible_id = Column(String, ForeignKey("users.id"), nullable=False)
    movement_type = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    observation = Column(String, nullable=True)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    reservation_id = Column(String, ForeignKey("reservations.id"), nullable=False)
    event = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    message = Column(String, nullable=False)
    status = Column(String, nullable=False, default="ENVIADA")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class ReservationItem(Base):
    __tablename__ = "reservation_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    reservation_id = Column(String, ForeignKey("reservations.id"), nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=False)
    start = Column(DateTime(timezone=True), nullable=False)
    end = Column(DateTime(timezone=True), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
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
    actor_id = Column(String, nullable=True)
    before_value = Column(String, nullable=True)
    after_value = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
