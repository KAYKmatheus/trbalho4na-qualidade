"""Availability-search checks for resource filters and occupied periods."""

from datetime import datetime, timezone

from app.models import Reservation, ReservationItem, ResourceBlock

START = "2026-12-01T09:00:00Z"
END = "2026-12-01T10:00:00Z"


def _token(client) -> dict[str, str]:
    login = client.post(
        "/v1/auth/login",
        json={"email": "requester@example.test", "password": "requester-password"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _create_resource(client, payload) -> str:
    admin_login = client.post(
        "/v1/auth/login",
        json={"email": "admin@example.test", "password": "correct-password"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    response = client.post("/v1/admin/resources", json=payload, headers=admin_headers)
    assert response.status_code == 201
    return response.json()["id"]


def test_ct08_search_applies_type_capacity_location_competency_and_period(auth_client) -> None:
    client, _ = auth_client
    headers = _token(client)
    _create_resource(
        client,
        {
            "resource_type": "sala",
            "name": "Sala de matemática",
            "category": "laboratório",
            "capacity": 32,
            "location": "Bloco A",
        },
    )
    _create_resource(
        client,
        {"resource_type": "sala", "name": "Sala pequena", "category": "aula", "capacity": 12, "location": "Bloco B"},
    )
    _create_resource(
        client,
        {"resource_type": "professor", "name": "Docente", "competencies": ["Matemática"]},
    )

    rooms = client.get(
        "/v1/resources/search",
        params={"resource_type": "sala", "capacity": 30, "location": "bloco a", "start": START, "end": END},
        headers=headers,
    )
    teachers = client.get(
        "/v1/resources/search",
        params={"resource_type": "professor", "competency": "matemática", "start": START, "end": END},
        headers=headers,
    )

    assert rooms.status_code == 200
    assert [resource["name"] for resource in rooms.json()] == ["Sala de matemática"]
    assert teachers.status_code == 200
    assert [resource["name"] for resource in teachers.json()] == ["Docente"]


def test_ct09_search_excludes_blocked_and_occupied_resources(auth_client) -> None:
    client, session = auth_client
    headers = _token(client)
    blocked_id = _create_resource(
        client,
        {
            "resource_type": "sala",
            "name": "Sala manutenção",
            "category": "aula",
            "capacity": 20,
            "location": "Bloco C",
        },
    )
    occupied_id = _create_resource(
        client,
        {
            "resource_type": "sala",
            "name": "Sala ocupada",
            "category": "aula",
            "capacity": 20,
            "location": "Bloco C",
        },
    )
    session.add(
        ResourceBlock(
            resource_id=blocked_id,
            start=datetime(2026, 12, 1, 8, tzinfo=timezone.utc),
            end=datetime(2026, 12, 1, 11, tzinfo=timezone.utc),
            reason="manutenção",
            status="ATIVO",
        )
    )
    reservation = Reservation(solicitante_id="requester-1", reason="Reserva existente")
    session.add(reservation)
    session.flush()
    session.add(
        ReservationItem(
            reservation_id=reservation.id,
            resource_type="sala",
            resource_id=occupied_id,
            start=datetime(2026, 12, 1, 8, tzinfo=timezone.utc),
            end=datetime(2026, 12, 1, 11, tzinfo=timezone.utc),
            status="CONFIRMADA",
        )
    )
    session.commit()

    response = client.get(
        "/v1/resources/search",
        params={"resource_type": "sala", "start": START, "end": END},
        headers=headers,
    )

    assert response.status_code == 200
    assert blocked_id not in {resource["id"] for resource in response.json()}
    assert occupied_id not in {resource["id"] for resource in response.json()}
