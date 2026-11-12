"""Create isolated PostgreSQL accounts, restricted rooms, scopes, and JMeter CSV."""

from __future__ import annotations

import csv
import os
import secrets
from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.db import init_db
from app.models import Resource, ResourceScope, User
from app.servicos.autenticacao import hash_password

ACCOUNT_COUNT = 100


def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("Defina DATABASE_URL para um banco PostgreSQL de teste.")

    database = make_url(database_url)
    if database.get_backend_name() != "postgresql":
        raise SystemExit("DATABASE_URL precisa apontar para PostgreSQL.")
    if "test" not in (database.database or "").lower():
        raise SystemExit("Por segurança, o nome do banco em DATABASE_URL deve conter 'test'.")

    database_url = database.set(drivername="postgresql+psycopg").render_as_string(hide_password=False)
    engine = create_engine(database_url, future=True)
    try:
        init_db(engine)
        session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        suffix = uuid4().hex
        rows: list[dict[str, str]] = []
        users: list[User] = []
        resources: list[Resource] = []
        scopes: list[ResourceScope] = []

        for index in range(1, ACCOUNT_COUNT + 1):
            requester_password = secrets.token_urlsafe(24)
            responsible_password = secrets.token_urlsafe(24)
            requester = User(
                id=uuid4().hex,
                name=f"Solicitante de carga {index:03d}",
                email=f"solicitante-{suffix}-{index:03d}@example.test",
                password_hash=hash_password(requester_password),
                role="SOLICITANTE",
                active=True,
            )
            responsible = User(
                id=uuid4().hex,
                name=f"Responsavel de carga {index:03d}",
                email=f"responsavel-{suffix}-{index:03d}@example.test",
                password_hash=hash_password(responsible_password),
                role="RESPONSAVEL",
                active=True,
            )
            room = Resource(
                id=uuid4().hex,
                resource_type="sala",
                name=f"Sala restrita {suffix[:8]}-{index:03d}",
                category="aula",
                capacity=30,
                location="Ambiente de teste de carga",
                restricted=True,
                active=True,
            )
            users.extend((requester, responsible))
            resources.append(room)
            scopes.append(ResourceScope(responsible_id=responsible.id, resource_id=room.id))
            rows.append(
                {
                    "requester_email": requester.email,
                    "requester_password": requester_password,
                    "responsible_email": responsible.email,
                    "responsible_password": responsible_password,
                    "resource_id": room.id,
                }
            )

        with session_factory.begin() as session:
            session.add_all(users)
            session.flush()
            session.add_all(resources)
            session.flush()
            session.add_all(scopes)

        csv_path = Path(__file__).with_name("reservas.csv")
        with csv_path.open("w", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

        print(f"Criadas {ACCOUNT_COUNT} contas solicitantes, 100 responsáveis e 100 salas restritas.")
        print(f"CSV de credenciais gerado em: {csv_path}")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
