"""HTTP tests for the EM_USO reservation lifecycle."""

import pytest

from app.models import Reservation, ReservationItem

START = "2026-12-10T09:00:00Z"
END = "2026-12-10T10:00:00Z"


def _token(client, email: str, password: str) -> dict[str, str]:
    response = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _reservation_in_use(client, session) -> str:
    admin = _token(client, "admin@example.test", "correct-password")
    requester = _token(client, "requester@example.test", "requester-password")
    resource = client.post(
        "/v1/admin/resources",
        headers=admin,
        json={
            "resource_type": "sala",
            "name": "Sala de teste EM_USO",
            "category": "aula",
            "capacity": 20,
            "location": "Bloco A",
        },
    )
    assert resource.status_code == 201
    created = client.post(
        "/v1/reservations",
        headers=requester,
        json={
            "solicitante_id": "untrusted",
            "reason": "Teste transição EM_USO",
            "items": [
                {
                    "resource_type": "sala",
                    "resource_id": resource.json()["id"],
                    "start": START,
                    "end": END,
                }
            ],
        },
    )
    assert created.status_code == 201
    reservation_id = created.json()["id"]
    session.query(Reservation).filter_by(id=reservation_id).one().status = "EM_USO"
    session.query(ReservationItem).filter_by(reservation_id=reservation_id).one().status = "EM_USO"
    session.commit()
    return reservation_id


def test_cannot_cancel_reservation_in_use_over_http(auth_client) -> None:
    client, session = auth_client
    reservation_id = _reservation_in_use(client, session)
    requester = _token(client, "requester@example.test", "requester-password")

    response = client.delete(f"/v1/reservations/{reservation_id}", headers=requester)

    assert response.status_code == 409, response.text
    assert "Transição de EM_USO para CANCELADA não permitida." in response.json()["detail"]
    assert session.query(Reservation).filter_by(id=reservation_id).one().status == "EM_USO"


@pytest.mark.parametrize(
    "target_status",
    [
        "SOLICITADA",
        "PENDENTE",
        "APROVADA",
        "CONFIRMADA",
        "REJEITADA",
        "CANCELADA",
        "NAO_COMPARECEU",
    ],
    ids=[
        "solicitada",
        "pendente",
        "aprovada",
        "confirmada",
        "rejeitada",
        "cancelada",
        "nao-compareceu",
    ],
)
def test_in_use_reservation_rejects_all_transitions_except_completion_over_http(
    auth_client,
    target_status: str,
) -> None:
    client, session = auth_client
    reservation_id = _reservation_in_use(client, session)
    admin = _token(client, "admin@example.test", "correct-password")

    response = client.patch(
        f"/v1/reservations/{reservation_id}/status",
        headers=admin,
        json={"status": target_status},
    )

    assert response.status_code == 409, response.text
    assert f"Transição de EM_USO para {target_status} não permitida." in response.json()["detail"]
    assert session.query(Reservation).filter_by(id=reservation_id).one().status == "EM_USO"


def test_in_use_reservation_can_be_completed_over_http(auth_client) -> None:
    client, session = auth_client
    reservation_id = _reservation_in_use(client, session)
    admin = _token(client, "admin@example.test", "correct-password")

    response = client.patch(
        f"/v1/reservations/{reservation_id}/status",
        headers=admin,
        json={"status": "CONCLUIDA"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CONCLUIDA"
