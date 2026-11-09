"""Persistence models and the transactional boundary for the reservation system."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    create_engine,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from app_config import AppSettings

Base = declarative_base()


Engine = None
SessionLocal = None


def configure_database(settings: AppSettings | None = None) -> None:
    """Initialise the database session using the runtime settings."""
    global Engine, SessionLocal
    settings = settings or AppSettings()
    Engine = create_engine(settings.database_url, future=True)
    SessionLocal = sessionmaker(
        bind=Engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )


configure_database()


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    solicitante_id = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    status = Column(String, nullable=False, default="PENDENTE")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    items = relationship("ReservationItem", back_populates="reservation", cascade="all, delete-orphan")


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
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    reservation = relationship("Reservation", back_populates="items")

    __table_args__ = (
        CheckConstraint('start < "end"', name="ck_reservation_item_valid_interval"),
        CheckConstraint("quantity > 0", name="ck_reservation_item_positive_quantity"),
        ExcludeConstraint(
            ("resource_type", "="),
            ("resource_id", "="),
            (func.tstzrange(start, end, "[)"), "&&"),
            where=text(
                "resource_type <> 'material' AND status IN "
                "('PENDENTE', 'APROVADA', 'CONFIRMADA')"
            ),
            using="gist",
            name="excl_active_resource_reservation_interval",
        ),
    )


class Material(Base):
    __tablename__ = "materials"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    quantity_total = Column(Integer, nullable=False)
    active = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint("quantity_total >= 0", name="ck_material_nonnegative_quantity"),
    )


class AuditEntry(Base):
    __tablename__ = "audit_entries"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    payload = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))



def init_db(database_url: str | None = None) -> None:
    """Create the minimal schema required by the PRD backbone.

    By keeping the schema intentionally narrow we preserve the domain model while
    avoiding speculative features that are not defined in the documentation.
    """
    url = database_url or AppSettings().database_url
    engine = create_engine(url, future=True)
    try:
        if engine.dialect.name == "postgresql":
            with engine.begin() as connection:
                connection.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
        Base.metadata.create_all(engine)
    finally:
        engine.dispose()


def execute_sql(sql_text: str, database_url: str | None = None) -> Any:
    """Run a raw SQL statement against PostgreSQL."""
    url = database_url or AppSettings().database_url
    engine = create_engine(url, future=True)
    with engine.begin() as conn:
        result = conn.execute(text(sql_text))
        return result
