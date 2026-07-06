from tests.conftest import login_token


def auth_headers(client):
    token = login_token(client, "admin@test.local")
    return {"Authorization": f"Bearer {token}"}


def test_create_patient_without_oib_succeeds(client, auth_setup):
    response = client.post(
        "/api/patients",
        headers=auth_headers(client),
        json={"first_name": "Bez", "last_name": "Oiba"},
    )

    assert response.status_code == 200
    assert response.json()["oib"] is None


def test_create_patient_with_valid_oib_succeeds_and_is_returned(client, auth_setup):
    response = client.post(
        "/api/patients",
        headers=auth_headers(client),
        json={"first_name": "Oib", "last_name": "Valjan", "oib": "12345678901"},
    )

    assert response.status_code == 200
    assert response.json()["oib"] == "12345678901"


def test_invalid_oib_is_rejected(client, auth_setup):
    response = client.post(
        "/api/patients",
        headers=auth_headers(client),
        json={"first_name": "Oib", "last_name": "Los", "oib": "ABC"},
    )

    assert response.status_code == 422


def test_duplicate_oib_is_rejected(client, auth_setup):
    headers = auth_headers(client)
    first = client.post("/api/patients", headers=headers, json={"first_name": "Prvi", "last_name": "Pacijent", "oib": "22222222222"})
    second = client.post("/api/patients", headers=headers, json={"first_name": "Drugi", "last_name": "Pacijent", "oib": "22222222222"})

    assert first.status_code == 200
    assert second.status_code == 409


def test_patient_search_includes_oib(client, auth_setup):
    headers = auth_headers(client)
    client.post("/api/patients", headers=headers, json={"first_name": "Search", "last_name": "Oib", "oib": "33333333333"})

    response = client.get("/api/patients?q=33333333333", headers=headers)

    assert response.status_code == 200
    assert [patient["oib"] for patient in response.json()] == ["33333333333"]
