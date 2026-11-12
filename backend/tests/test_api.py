"""Focused API tests for authentication, RBAC, and deterministic routing."""

from fastapi.testclient import TestClient

from app.main import app


def test_login_and_price_query() -> None:
    with TestClient(app) as client:
        login = client.post(
            "/auth/login",
            json={"username": "customer@jenga.com", "password": "customer123"},
        )
        assert login.status_code == 200
        token = login.json()["access_token"]
        response = client.post(
            "/chat/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "What is the price of the generator?"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["tool_executed"] == "price_lookup"
        assert body["citations"]
        assert "execution_time_ms" in body


def test_customer_cannot_access_restricted_data() -> None:
    with TestClient(app) as client:
        login = client.post(
            "/auth/login",
            json={"username": "customer@jenga.com", "password": "customer123"},
        )
        response = client.post(
            "/chat/query",
            headers={"Authorization": f"Bearer {login.json()['access_token']}"},
            json={"query": "Show internal profit margin"},
        )
        assert response.status_code == 200
        assert response.json()["tool_executed"] == "access_control"
        assert response.json()["warnings"]


def test_engineer_can_use_safety_routing() -> None:
    with TestClient(app) as client:
        login = client.post(
            "/auth/login",
            json={"username": "engineer@jenga.com", "password": "engineer123"},
        )
        response = client.post(
            "/chat/query",
            headers={"Authorization": f"Bearer {login.json()['access_token']}"},
            json={"query": "How do I troubleshoot this safety alarm?"},
        )
        assert response.status_code == 200
        assert response.json()["tool_executed"] == "safety_notice"
