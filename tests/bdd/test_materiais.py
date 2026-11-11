"""Material checkout, return, and pending-balance checks."""

from app.models import MaterialMovement, Reservation, ReservationItem

START = "2026-12-22T09:00:00Z"
END = "2026-12-22T10:00:00Z"


def _headers(client, email: str, password: str) -> dict[str, str]:
    login = client.post("/v1/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _material_item(client, admin_headers, requester_headers, *, quantity: int, total: int):
    resource_response = client.post(
        "/v1/admin/resources",
        headers=admin_headers,
        json={
            "resource_type": "material",
            "name": f"Material {quantity} de {total}",
            "category": "equipamento",
            "quantity_total": total,
        },
    )
    assert resource_response.status_code == 201
    resource = resource_response.json()
    reservation = client.post(
        "/v1/reservations",
        headers=requester_headers,
        json={
            "solicitante_id": "untrusted",
            "reason": "Atividade com material",
            "items": [
                {
                    "resource_type": "material",
                    "resource_id": resource["id"],
                    "start": START,
                    "end": END,
                    "quantity": quantity,
                }
            ],
        },
    )
    assert reservation.status_code == 201
    return resource, reservation.json(), reservation.json()["items"][0]["id"]


def _assign_responsible(client, admin_headers, resource_id: str) -> None:
    response = client.post(
        "/v1/admin/responsaveis/responsible-1/recursos",
        headers=admin_headers,
        json={"resource_id": resource_id},
    )
    assert response.status_code == 201


def test_ct25_withdrawal_and_return_balance_is_calculated(auth_client) -> None:
    client, session = auth_client
    admin = _headers(client, "admin@example.test", "correct-password")
    requester = _headers(client, "requester@example.test", "requester-password")
    responsible = _headers(client, "responsible@example.test", "responsible-password")
    resource, _, item_id = _material_item(client, admin, requester, quantity=3, total=5)
    _assign_responsible(client, admin, resource["id"])

    withdrawal = client.post(
        f"/v1/reservations/items/{item_id}/movements",
        headers=responsible,
        json={"movement_type": "RETIRADA", "quantity": 3},
    )
    returned = client.post(
        f"/v1/reservations/items/{item_id}/movements",
        headers=responsible,
        json={"movement_type": "DEVOLUCAO", "quantity": 2},
    )
    balance = client.get(f"/v1/reservations/items/{item_id}/material-balance", headers=responsible)

    assert withdrawal.status_code == 201
    assert returned.status_code == 201
    assert balance.json()["pending"] == 1
    assert (
        session.query(MaterialMovement)
        .join(ReservationItem, ReservationItem.id == MaterialMovement.reservation_item_id)
        .filter(ReservationItem.resource_id == resource["id"])
        .count()
        == 2
    )


def test_ct26_return_above_withdrawn_units_is_rejected_without_record(auth_client) -> None:
    client, session = auth_client
    admin = _headers(client, "admin@example.test", "correct-password")
    requester = _headers(client, "requester@example.test", "requester-password")
    responsible = _headers(client, "responsible@example.test", "responsible-password")
    resource, _, item_id = _material_item(client, admin, requester, quantity=2, total=4)
    _assign_responsible(client, admin, resource["id"])
    client.post(
        f"/v1/reservations/items/{item_id}/movements",
        headers=responsible,
        json={"movement_type": "RETIRADA", "quantity": 1},
    )

    excessive_return = client.post(
        f"/v1/reservations/items/{item_id}/movements",
        headers=responsible,
        json={"movement_type": "DEVOLUCAO", "quantity": 2},
    )

    assert excessive_return.status_code == 422
    assert session.query(MaterialMovement).filter_by(movement_type="DEVOLUCAO").count() == 0


def test_ct27_unreturned_material_remains_unavailable(auth_client) -> None:
    client, session = auth_client
    admin = _headers(client, "admin@example.test", "correct-password")
    requester = _headers(client, "requester@example.test", "requester-password")
    responsible = _headers(client, "responsible@example.test", "responsible-password")
    resource, reservation, item_id = _material_item(client, admin, requester, quantity=1, total=1)
    _assign_responsible(client, admin, resource["id"])
    client.post(
        f"/v1/reservations/items/{item_id}/movements",
        headers=responsible,
        json={"movement_type": "RETIRADA", "quantity": 1},
    )
    session.query(ReservationItem).filter_by(id=item_id).one().status = "CONCLUIDA"
    session.query(Reservation).filter_by(id=reservation["id"]).one().status = "CONCLUIDA"
    session.commit()

    balance = client.get(f"/v1/reservations/items/{item_id}/material-balance", headers=responsible)
    available = client.get(
        "/v1/resources/search",
        headers=requester,
        params={"resource_type": "material", "start": START, "end": END, "quantity": 1},
    )

    assert balance.status_code == 200
    assert balance.json()["pending"] == 1
    assert resource["id"] not in {item["id"] for item in available.json()}
