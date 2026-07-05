def test_public_config_exposes_demo_guardrails(client):
    response = client.get("/api/public-config")

    assert response.status_code == 200
    payload = response.json()
    assert payload["app_name"] == "ASTRA Clinic Core"
    assert payload["demo_mode"] is True
    assert payload["real_data_allowed"] is False
    assert payload["fiscalization_mode"] == "noop"
    assert "jwt" not in str(payload).lower()
    assert response.headers["X-ASTRA-REAL-DATA-ALLOWED"] == "false"
