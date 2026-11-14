"""Testes de autorização dos painéis do Administrador e Responsável."""

from datetime import datetime, timezone

from app.models import Reservation, ReservationItem, Resource, ResourceScope


def login(client, email, password):
    response = client.post(
        "/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }


def test_solicitante_nao_pode_listar_usuarios(auth_client):
    client, _ = auth_client
    headers = login(client, "requester@example.test", "requester-password")

    response = client.get("/v1/admin/users", headers=headers)

    assert response.status_code == 403


def test_responsavel_nao_pode_listar_usuarios(auth_client):
    client, _ = auth_client
    headers = login(client, "responsible@example.test", "responsible-password")

    response = client.get("/v1/admin/users", headers=headers)

    assert response.status_code == 403


def test_admin_lista_usuarios_sem_expor_senhas(auth_client):
    client, _ = auth_client
    headers = login(client, "admin@example.test", "correct-password")

    response = client.get("/v1/admin/users", headers=headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

    for usuario in response.json():
        assert "password" not in usuario
        assert "password_hash" not in usuario


def test_solicitante_nao_pode_consultar_pendencias(auth_client):
    client, _ = auth_client
    headers = login(client, "requester@example.test", "requester-password")

    response = client.get("/v1/responsavel/pendencias", headers=headers)

    assert response.status_code == 403


def test_responsavel_ve_apenas_pendencias_do_seu_escopo(auth_client):
    client, session = auth_client

    sala_permitida = Resource(
        resource_type="sala",
        name="Sala permitida",
        category="aula",
        capacity=30,
        location="Bloco A",
        restricted=True,
        active=True,
    )

    sala_nao_permitida = Resource(
        resource_type="sala",
        name="Sala fora do escopo",
        category="aula",
        capacity=30,
        location="Bloco B",
        restricted=True,
        active=True,
    )

    session.add_all([sala_permitida, sala_nao_permitida])
    session.flush()

    session.add(
        ResourceScope(
            responsible_id="responsible-1",
            resource_id=sala_permitida.id,
        )
    )

    inicio = datetime(2026, 12, 20, 14, tzinfo=timezone.utc)
    fim = datetime(2026, 12, 20, 15, tzinfo=timezone.utc)

    for sala in [sala_permitida, sala_nao_permitida]:
        reserva = Reservation(
            solicitante_id="requester-1",
            reason="Teste de escopo",
            status="PENDENTE",
        )
        session.add(reserva)
        session.flush()

        session.add(
            ReservationItem(
                reservation_id=reserva.id,
                resource_type="sala",
                resource_id=sala.id,
                start=inicio,
                end=fim,
                status="PENDENTE",
            )
        )

    session.commit()

    headers = login(client, "responsible@example.test", "responsible-password")

    response = client.get("/v1/responsavel/pendencias", headers=headers)

    assert response.status_code == 200

    nomes = {item["resource_name"] for item in response.json()}

    assert "Sala permitida" in nomes
    assert "Sala fora do escopo" not in nomes
