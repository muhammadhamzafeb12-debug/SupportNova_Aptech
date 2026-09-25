"""
FastAPI Endpoints Test Suite
"""
from fastapi.testclient import TestClient
from backend.src.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_login_flow():
    # Test valid login
    response = client.post("/auth/login", json={
        "username": "admin@nexalink.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["role"] == "Admin"

    access_token = data["access_token"]

    # Test /auth/me with bearer token
    me_resp = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["username"] == "admin@nexalink.com"
    assert me_data["role"] == "Admin"

def test_complaints_endpoints():
    login_resp = client.post("/auth/login", json={
        "username": "customer@nexalink.com",
        "password": "password123"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # List complaints
    res = client.get("/complaints", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # Create new complaint
    new_cmp = client.post("/complaints", headers=headers, json={
        "customer_email": "customer@nexalink.com",
        "customer_name": "Sarah Jenkins",
        "account_number": "ACC-994821",
        "title": "Fiber speed issue",
        "category": "Network Outages & Fiber Disconnection",
        "description": "Fiber internet speed is slower than 1Gbps subscribed tier.",
        "requested_credit": 25.0
    })
    assert new_cmp.status_code == 201
    created_data = new_cmp.json()
    assert created_data["complaint_number"].startswith("CMP-2026-")

def test_rule_matrix_and_knowledge_base():
    login_resp = client.post("/auth/login", json={
        "username": "admin@nexalink.com",
        "password": "password123"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Rule matrix
    rm_res = client.get("/rule_matrix", headers=headers)
    assert rm_res.status_code == 200
    assert len(rm_res.json()) >= 10

    # Knowledge base search
    kb_res = client.get("/knowledge_base?query=SLA", headers=headers)
    assert kb_res.status_code == 200
    assert isinstance(kb_res.json(), list)
