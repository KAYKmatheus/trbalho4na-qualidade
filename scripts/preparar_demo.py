"""Prepara contas fictícias para demonstração acadêmica."""

import os
import secrets
from uuid import uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.db import init_db
from app.models import Resource, ResourceScope, User
from app.servicos.autenticacao import hash_password


def main():
    url = os.getenv("DATABASE_URL")

    if not url:
        raise SystemExit("Defina DATABASE_URL antes de executar.")

    parsed = make_url(url)

    if (
        parsed.get_backend_name() != "postgresql"
        or "test" not in (parsed.database or "").lower()
    ):
        raise SystemExit(
            "Por segurança, use somente um banco PostgreSQL de teste."
        )

    engine = create_engine(url, future=True)

    contas = [
        ("Administrador Demo", "admin@demo.local", "ADMIN"),
        ("Responsavel Demo", "responsavel@demo.local", "RESPONSAVEL"),
        ("Solicitante Demo", "solicitante@demo.local", "SOLICITANTE"),
    ]

    try:
        init_db(engine)

        with Session(engine) as session:
            credenciais = {}
            usuarios = {}

            for nome, email, perfil in contas:
                usuario = session.scalar(
                    select(User).where(User.email == email)
                )

                if usuario is None:
                    senha = secrets.token_urlsafe(18)
                    usuario = User(
                        id=str(uuid4()),
                        name=nome,
                        email=email,
                        password_hash=hash_password(senha),
                        role=perfil,
                        active=True,
                    )
                    session.add(usuario)
                    credenciais[email] = senha

                usuarios[perfil] = usuario

            session.flush()

            sala = session.scalar(
                select(Resource).where(
                    Resource.name == "Sala Demonstracao AlocaSenac"
                )
            )

            if sala is None:
                sala = Resource(
                    id=str(uuid4()),
                    resource_type="sala",
                    name="Sala Demonstracao AlocaSenac",
                    category="aula",
                    capacity=30,
                    location="Ambiente demonstrativo",
                    restricted=True,
                    active=True,
                )
                session.add(sala)
                session.flush()

            responsavel = usuarios["RESPONSAVEL"]

            escopo = session.scalar(
                select(ResourceScope).where(
                    ResourceScope.responsible_id == responsavel.id,
                    ResourceScope.resource_id == sala.id,
                )
            )

            if escopo is None:
                session.add(
                    ResourceScope(
                        responsible_id=responsavel.id,
                        resource_id=sala.id,
                    )
                )

            session.commit()

        print("\n=== CONTAS DE DEMONSTRACAO ===")

        for nome, email, perfil in contas:
            print(f"\nPerfil: {perfil}")
            print(f"Email: {email}")
            if email in credenciais:
                print(f"Senha: {credenciais[email]}")
            else:
                print("Conta ja existente; senha preservada.")

        print("\nSala de demonstracao preparada.")
        print("Nao publique as senhas no GitHub.")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
