"""Administrative resource and responsibility-scope checks."""

from datetime import datetime, timezone

from app.models import AuditEntry, Reservation, ReservationItem, Resource, ResourceScope


def _admin_headers(client) -> dict[str, str]:
    login = client.post(
        "/v1/auth/login",
        json={"email": "admin@example.test", "password": "correct-password"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_ct06_admin_creates_updates_and_queries_resource_types(auth_client) -> None:
    client, session = auth_client
    headers = _admin_headers(client)
    bodies = [
        {"resource_type": "sala", "name": "Sala 1", "category": "laboratório", "capacity": 24, "location": "Bloco A"},
        {"resource_type": "professor", "name": "Ana", "competencies": ["Química"]},
        {"resource_type": "material", "name": "Projetor", "category": "audiovisual", "quantity_total": 3},
    ]

    created = [
        client.post("/v1/admin/resources", json=body, headers=headers)
        for body in bodies
    ]
    assert [response.status_code for response in created] == [201, 201, 201]

    room_id = created[0].json()["id"]
    updated = client.patch(
        f"/v1/admin/resources/{room_id}",
        json={"capacity": 30},
        headers=headers,
    )
    queried = client.get(f"/v1/admin/resources/{room_id}", headers=headers)

    assert updated.status_code == 200
    assert queried.status_code == 200
    assert queried.json()["capacity"] == 30
    assert session.query(Resource).count() == 3
    assert session.query(AuditEntry).count() == 4


def test_ct07_deactivating_resource_preserves_reservation_history(auth_client) -> None:
    client, session = auth_client
    headers = _admin_headers(client)
    response = client.post(
        "/v1/admin/resources",
        json={
            "resource_type": "sala",
            "name": "Sala histórica",
            "category": "sala de aula",
            "capacity": 10,
            "location": "Bloco B",
        },
        headers=headers,
    )
    resource_id = response.json()["id"]
    reservation = Reservation(solicitante_id="requester-1", reason="Aula histórica")
    session.add(reservation)
    session.flush()
    session.add(
        ReservationItem(
            reservation_id=reservation.id,
            resource_type="sala",
            resource_id=resource_id,
            start=datetime(2026, 11, 1, 9, tzinfo=timezone.utc),
            end=datetime(2026, 11, 1, 10, tzinfo=timezone.utc),
            status="CANCELADA",
        )
    )
    session.commit()

    deactivated = client.patch(
        f"/v1/admin/resources/{resource_id}",
        json={"active": False},
        headers=headers,
    )

    assert deactivated.status_code == 200
    assert deactivated.json()["active"] is False
    assert session.query(ReservationItem).filter_by(resource_id=resource_id).count() == 1


def test_ct40_admin_assigns_and_removes_responsible_scope_with_audit(auth_client) -> None:
    client, session = auth_client
    headers = _admin_headers(client)
    resource = client.post(
        "/v1/admin/resources",
        json={"resource_type": "professor", "name": "Professor escopo"},
        headers=headers,
    ).json()

    assigned = client.post(
        "/v1/admin/responsaveis/responsible-1/recursos",
        json={"resource_id": resource["id"]},
        headers=headers,
    )
    assert assigned.status_code == 201
    assert session.query(ResourceScope).filter_by(
        responsible_id="responsible-1",
        resource_id=resource["id"],
    ).count() == 1

    removed = client.delete(
        f"/v1/admin/responsaveis/responsible-1/recursos/{resource['id']}",
        headers=headers,
    )

    assert removed.status_code == 204
    assert session.query(ResourceScope).filter_by(resource_id=resource["id"]).count() == 0
    assert session.query(AuditEntry).filter(AuditEntry.action.in_(("SCOPE_ADD", "SCOPE_REMOVE"))).count() == 2
