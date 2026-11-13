"""Utilization and avoided-conflict reporting checks."""

from datetime import datetime, timezone

import pytest

from app.erros import ValidationError
from app.models import AuditEntry, Reservation, ReservationItem, ResourceScope
from app.servicos.relatorios import ReportService

REPORT_START = "2026-11-01T00:00:00Z"
REPORT_END = "2026-12-28T00:00:00Z"
RESERVATION_START = "2026-12-27T09:00:00Z"
RESERVATION_END = "2026-12-27T10:30:00Z"


def _headers(client, email: str, password: str) -> dict[str, str]:
    login = client.post("/v1/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _room(client, admin, name: str) -> dict:
    return client.post(
        "/v1/admin/resources",
        headers=admin,
        json={
            "resource_type": "sala",
            "name": name,
            "category": "aula",
            "capacity": 24,
            "location": "Bloco A",
        },
    ).json()


def _reserve(client, requester, room_id: str, start: str = RESERVATION_START, end: str = RESERVATION_END):
    return client.post(
        "/v1/reservations",
        headers=requester,
        json={
            "solicitante_id": "untrusted",
            "reason": "Atividade acadêmica",
            "items": [{"resource_type": "sala", "resource_id": room_id, "start": start, "end": end}],
        },
    )


def _report(client, headers):
    return client.get(
        "/v1/admin/reports",
        headers=headers,
        params={"start": REPORT_START, "end": REPORT_END},
    )


def test_ct31_report_contains_utilization_teaching_load_and_conflict_count(auth_client) -> None:
    client, _ = auth_client
    admin = _headers(client, "admin@example.test", "correct-password")
    requester = _headers(client, "requester@example.test", "requester-password")
    room = _room(client, admin, "Sala relatório")
    assert _reserve(client, requester, room["id"]).status_code == 201

    report = _report(client, admin)

    assert report.status_code == 200
    result = report.json()
    assert result["utilization"][0]["resource_id"] == room["id"]
    assert result["utilization"][0]["reservation_count"] == 1
    assert result["utilization"][0]["allocated_hours"] == 1.5
    assert "teaching_hours" in result
    assert result["conflicts_avoided"] == 0


def test_ct32_conflict_counter_increases_for_each_refused_request(auth_client) -> None:
    client, session = auth_client
    admin = _headers(client, "admin@example.test", "correct-password")
    requester = _headers(client, "requester@example.test", "requester-password")
    room = _room(client, admin, "Sala contador")
    assert _reserve(client, requester, room["id"]).status_code == 201
    before = _report(client, admin).json()["conflicts_avoided"]

    first = _reserve(client, requester, room["id"])
    second = _reserve(client, requester, room["id"])
    after = _report(client, admin).json()["conflicts_avoided"]

    assert first.status_code == 409
    assert second.status_code == 409
    assert after - before == 2
    assert session.query(AuditEntry).filter_by(action="CONFLITO_EVITADO", entity_id=room["id"]).count() == 2


def test_ct38_avoided_conflict_event_has_actor_resource_interval_and_reason(auth_client) -> None:
    client, session = auth_client
    admin = _headers(client, "admin@example.test", "correct-password")
    requester = _headers(client, "requester@example.test", "requester-password")
    room = _room(client, admin, "Sala evento conflito")
    _reserve(client, requester, room["id"])
    refused = _reserve(client, requester, room["id"])

    event = session.query(AuditEntry).filter_by(action="CONFLITO_EVITADO", entity_id=room["id"]).one()

    assert refused.status_code == 409
    assert event.entity_type == "sala"
    assert event.actor_id == "requester-1"
    assert "SOBREPOSICAO" in event.payload
    assert "2026-12-27T09:00:00" in event.payload
    assert "2026-12-27T10:30:00" in event.payload


@pytest.mark.parametrize(
    ("start", "end"),
    [
        (datetime(2026, 12, 1), datetime(2026, 12, 2, tzinfo=timezone.utc)),
        (datetime(2026, 12, 1, tzinfo=timezone.utc), datetime(2026, 12, 2)),
    ],
)
def test_report_rejects_naive_period_boundaries(auth_client, start: datetime, end: datetime) -> None:
    _, session = auth_client

    with pytest.raises(ValidationError, match="fuso horário"):
        ReportService(session).generate(start=start, end=end, user_id="admin-1", role="ADMIN")


def test_responsible_report_with_no_scoped_resources_is_empty(auth_client) -> None:
    _, session = auth_client

    report = ReportService(session).generate(
        start=datetime(2026, 11, 1, tzinfo=timezone.utc),
        end=datetime(2026, 12, 28, tzinfo=timezone.utc),
        user_id="responsible-1",
        role="RESPONSAVEL",
    )

    assert report["utilization"] == []
    assert report["teaching_hours"] == 0
    assert report["conflicts_avoided"] == 0


def test_responsible_report_includes_only_scoped_resources_and_conflicts(auth_client) -> None:
    client, session = auth_client
    admin = _headers(client, "admin@example.test", "correct-password")
    requester = _headers(client, "requester@example.test", "requester-password")
    scoped_room = _room(client, admin, "Sala escopo relatório")
    other_room = _room(client, admin, "Sala fora do escopo")
    assert _reserve(client, requester, scoped_room["id"]).status_code == 201
    assert _reserve(client, requester, other_room["id"]).status_code == 201

    conflict_time = datetime(2026, 12, 15, tzinfo=timezone.utc)
    session.add_all(
        [
            ResourceScope(responsible_id="responsible-1", resource_id=scoped_room["id"]),
            AuditEntry(
                entity_type="sala",
                entity_id=scoped_room["id"],
                action="CONFLITO_EVITADO",
                payload="{}",
                created_at=conflict_time,
            ),
            AuditEntry(
                entity_type="sala",
                entity_id=other_room["id"],
                action="CONFLITO_EVITADO",
                payload="{}",
                created_at=conflict_time,
            ),
        ]
    )
    session.commit()

    report = ReportService(session).generate(
        start=datetime(2026, 11, 1, tzinfo=timezone.utc),
        end=datetime(2026, 12, 28, tzinfo=timezone.utc),
        user_id="responsible-1",
        role="RESPONSAVEL",
    )

    assert [row["resource_id"] for row in report["utilization"]] == [scoped_room["id"]]
    assert report["conflicts_avoided"] == 1


def test_report_uses_resource_id_when_resource_record_is_missing(auth_client) -> None:
    _, session = auth_client
    start = datetime(2026, 12, 27, 9, tzinfo=timezone.utc)
    end = datetime(2026, 12, 27, 10, 30, tzinfo=timezone.utc)
    session.add(
        Reservation(
            id="orphan-resource-reservation",
            solicitante_id="requester-1",
            reason="Relatório após remoção do recurso",
            status="CONFIRMADA",
        )
    )
    session.flush()
    session.add(
        ReservationItem(
            reservation_id="orphan-resource-reservation",
            resource_type="sala",
            resource_id="removed-resource",
            start=start,
            end=end,
            status="CONFIRMADA",
        )
    )
    session.commit()

    report = ReportService(session).generate(
        start=datetime(2026, 11, 1, tzinfo=timezone.utc),
        end=datetime(2026, 12, 28, tzinfo=timezone.utc),
        user_id="admin-1",
        role="ADMIN",
    )

    assert report["utilization"][0]["resource_name"] == "removed-resource"
