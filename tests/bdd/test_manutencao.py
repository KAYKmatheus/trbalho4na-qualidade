"""Maintenance-block reservation checks."""

from app.models import AuditEntry, ResourceBlock


def test_ct24_resource_in_maintenance_cannot_be_reserved(auth_client) -> None:
    client, session = auth_client
    admin_login = client.post(
        "/v1/auth/login",
        json={"email": "admin@example.test", "password": "correct-password"},
    )
    requester_login = client.post(
        "/v1/auth/login",
        json={"email": "requester@example.test", "password": "requester-password"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    requester_headers = {"Authorization": f"Bearer {requester_login.json()['access_token']}"}
    resource = client.post(
        "/v1/admin/resources",
        headers=admin_headers,
        json={
            "resource_type": "sala",
            "name": "Sala em manutenção",
            "category": "aula",
            "capacity": 24,
            "location": "Bloco A",
        },
    ).json()

    block = client.post(
        f"/v1/admin/resources/{resource['id']}/maintenance",
        headers=admin_headers,
        json={
            "start": "2026-12-20T08:00:00Z",
            "end": "2026-12-20T12:00:00Z",
            "reason": "Reparo elétrico",
        },
    )
    reservation = client.post(
        "/v1/reservations",
        headers=requester_headers,
        json={
            "solicitante_id": "untrusted",
            "reason": "Aula durante a manutenção",
            "items": [
                {
                    "resource_type": "sala",
                    "resource_id": resource["id"],
                    "start": "2026-12-20T09:00:00Z",
                    "end": "2026-12-20T10:00:00Z",
                }
            ],
        },
    )

    assert block.status_code == 201
    assert reservation.status_code == 409
    assert session.query(ResourceBlock).filter_by(resource_id=resource["id"]).count() == 1
    assert session.query(AuditEntry).filter_by(action="RESOURCE_BLOCK").count() == 1
