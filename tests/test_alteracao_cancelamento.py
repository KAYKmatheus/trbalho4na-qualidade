"""Reservation-change and cancellation checks."""

from datetime import datetime, timezone

from app.models import Reservation, ReservationItem

START = "2026-12-10T09:00:00Z"
END = "2026-12-10T10:00:00Z"


def _requester_headers(client) -> dict[str, str]:
    login = client.post(
        "/v1/auth/login",
        json={"email": "requester@example.test", "password": "requester-password"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _create_reservation(client, headers, resource_id: str):
    return client.post(
        "/v1/reservations",
        headers=headers,
        json={
            "solicitante_id": "ignored-client-id",
            "reason": "Aula de teste",
            "items": [
                {
                    "resource_type": "sala",
                    "resource_id": resource_id,
                    "start": START,
                    "end": END,
                }
            ],
        },
    )


def test_ct13_conflicting_change_returns_409_and_preserves_original(auth_client) -> None:
    client, session = auth_client
    headers = _requester_headers(client)
    admin = client.post(
        "/v1/auth/login",
        json={"email": "admin@example.test", "password": "correct-password"},
    )
    resource = client.post(
        "/v1/admin/resources",
        headers={"Authorization": f"Bearer {admin.json()['access_token']}"},
        json={
            "resource_type": "sala",
            "name": "Sala de alteração",
            "category": "aula",
            "capacity": 20,
            "location": "Bloco A",
            "restricted": True,
        },
    ).json()
    original = _create_reservation(client, headers, resource["id"])
    competing = _create_reservation(client, headers, resource["id"])
    assert original.status_code == 201
    assert competing.status_code == 201
    original_id = original.json()["id"]
    original_item = session.query(ReservationItem).filter_by(reservation_id=original_id).one()
    original_item.status = "CONFIRMADA"
    session.query(Reservation).filter_by(id=original_id).one().status = "CONFIRMADA"
    session.commit()

    changed = client.patch(
        f"/v1/reservations/{competing.json()['id']}",
        headers=headers,
        json={
            "reason": "Alteração em conflito",
            "items": [
                {
                    "resource_type": "sala",
                    "resource_id": resource["id"],
                    "start": "2026-12-10T09:30:00Z",
                    "end": "2026-12-10T10:30:00Z",
                }
            ],
        },
    )

    assert changed.status_code == 409
    preserved_item = session.query(ReservationItem).filter_by(reservation_id=competing.json()["id"]).one()
    assert preserved_item.start.replace(tzinfo=timezone.utc) == datetime(2026, 12, 10, 9, tzinfo=timezone.utc)
    assert session.query(Reservation).filter_by(id=competing.json()["id"]).one().reason == "Aula de teste"


def test_ct14_cancel_changes_state_and_releases_resource(auth_client) -> None:
    client, session = auth_client
    admin = client.post(
        "/v1/auth/login",
        json={"email": "admin@example.test", "password": "correct-password"},
    )
    resource = client.post(
        "/v1/admin/resources",
        headers={"Authorization": f"Bearer {admin.json()['access_token']}"},
        json={
            "resource_type": "sala",
            "name": "Sala cancelamento",
            "category": "aula",
            "capacity": 20,
            "location": "Bloco D",
        },
    ).json()
    headers = _requester_headers(client)
    created = _create_reservation(client, headers, resource["id"])
    reservation_id = created.json()["id"]
    session.query(ReservationItem).filter_by(reservation_id=reservation_id).one().status = "CONFIRMADA"
    session.commit()

    cancelled = client.delete(f"/v1/reservations/{reservation_id}", headers=headers)
    availability = client.get(
        "/v1/resources/search",
        params={"resource_type": "sala", "start": START, "end": END},
        headers=headers,
    )

    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "CANCELADA"
    assert resource["id"] in {item["id"] for item in availability.json()}


def test_ct04_requester_cannot_change_or_cancel_another_users_reservation(auth_client) -> None:
    client, session = auth_client
    admin = client.post(
        "/v1/auth/login",
        json={"email": "admin@example.test", "password": "correct-password"},
    ).json()["access_token"]
    requester_headers = _requester_headers(client)
    other_user = client.post(
        "/v1/admin/users",
        headers={"Authorization": f"Bearer {admin}"},
        json={
            "name": "Outro solicitante",
            "email": "other-requester@example.test",
            "password": "other-password",
            "role": "SOLICITANTE",
        },
    )
    other_headers = _requester_headers_for(client, "other-requester@example.test", "other-password")
    resource = client.post(
        "/v1/admin/resources",
        headers={"Authorization": f"Bearer {admin}"},
        json={
            "resource_type": "sala",
            "name": "Sala de propriedade",
            "category": "aula",
            "capacity": 20,
            "location": "Bloco A",
        },
    ).json()
    created = _create_reservation(client, requester_headers, resource["id"])
    reservation_id = created.json()["id"]

    changed = client.patch(
        f"/v1/reservations/{reservation_id}",
        headers=other_headers,
        json={"reason": "Tentativa não autorizada"},
    )
    cancelled = client.delete(f"/v1/reservations/{reservation_id}", headers=other_headers)

    assert other_user.status_code == 201
    assert changed.status_code == cancelled.status_code == 403
    assert session.query(Reservation).filter_by(id=reservation_id).one().reason == "Aula de teste"
    assert session.query(Reservation).filter_by(id=reservation_id).one().status != "CANCELADA"


def _requester_headers_for(client, email: str, password: str) -> dict[str, str]:
    login = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return {"Authorization": "Bearer " + login.json()["access_token"]}
