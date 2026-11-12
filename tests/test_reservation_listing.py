"""HTTP tests for requester-scoped reservation listing."""


def _token(client, email: str, password: str) -> dict[str, str]:
    response = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_requester_lists_only_their_own_reservations_over_http(auth_client) -> None:
    client, _ = auth_client
    admin = _token(client, "admin@example.test", "correct-password")
    requester = _token(client, "requester@example.test", "requester-password")
    second_user_response = client.post(
        "/v1/admin/users",
        headers=admin,
        json={
            "name": "Segundo solicitante",
            "email": "second-requester@example.test",
            "password": "second-password",
            "role": "SOLICITANTE",
        },
    )
    assert second_user_response.status_code == 201
    second_user = _token(client, "second-requester@example.test", "second-password")

    resource_ids = []
    for name in ("Sala lista própria 1", "Sala lista própria 2"):
        resource = client.post(
            "/v1/admin/resources",
            headers=admin,
            json={
                "resource_type": "sala",
                "name": name,
                "category": "aula",
                "capacity": 20,
                "location": "Bloco A",
            },
        )
        assert resource.status_code == 201
        resource_ids.append(resource.json()["id"])

    reservations = []
    for headers, resource_id, reason in (
        (requester, resource_ids[0], "Reserva do solicitante 1"),
        (second_user, resource_ids[1], "Reserva do solicitante 2"),
    ):
        response = client.post(
            "/v1/reservations",
            headers=headers,
            json={
                "solicitante_id": "id-fornecido-pelo-cliente-ignorado",
                "reason": reason,
                "items": [
                    {
                        "resource_type": "sala",
                        "resource_id": resource_id,
                        "start": "2026-12-20T09:00:00Z",
                        "end": "2026-12-20T10:00:00Z",
                    }
                ],
            },
        )
        assert response.status_code == 201
        reservations.append(response.json())

    first_list = client.get("/v1/reservations", headers=requester)
    second_list = client.get("/v1/reservations", headers=second_user)

    assert first_list.status_code == second_list.status_code == 200
    assert [reservation["id"] for reservation in first_list.json()] == [reservations[0]["id"]]
    assert [reservation["id"] for reservation in second_list.json()] == [reservations[1]["id"]]
