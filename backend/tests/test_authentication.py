import pytest

def test_valid_login(client):
    res = client.post("/api/auth/token", json={"username_or_email": "admin_user", "password": "pass123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "ADMIN"
    assert data["username"] == "admin_user"

def test_valid_login_via_email(client):
    res = client.post("/api/auth/token", json={"username_or_email": "customer_test@gmail.com", "password": "pass123"})
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "CUSTOMER"

def test_invalid_email(client):
    res = client.post("/api/auth/token", json={"username_or_email": "nonexistent@gmail.com", "password": "pass123"})
    assert res.status_code == 401
    assert "Invalid" in res.json()["detail"]

def test_invalid_password(client):
    res = client.post("/api/auth/token", json={"username_or_email": "admin_user", "password": "wrongpassword"})
    assert res.status_code == 401

def test_empty_credentials(client):
    res = client.post("/api/auth/token", json={"username_or_email": "", "password": ""})
    assert res.status_code == 400

def test_disabled_account(client):
    res = client.post("/api/auth/token", json={"username_or_email": "disabled_user", "password": "pass123"})
    assert res.status_code == 403
    assert "disabled" in res.json()["detail"].lower()

def test_logout(client):
    token = client.post("/api/auth/token", json={"username_or_email": "admin_user", "password": "pass123"}).json()["access_token"]
    res = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert "Successfully logged out" in res.json()["message"]

def test_protected_route_without_auth(client):
    res = client.get("/api/users")
    assert res.status_code == 401

def test_customer_accessing_admin_dashboard(client):
    token = client.post("/api/auth/token", json={"username_or_email": "customer_user", "password": "pass123"}).json()["access_token"]
    res = client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403

def test_agent_accessing_admin_dashboard(client):
    token = client.post("/api/auth/token", json={"username_or_email": "agent_user", "password": "pass123"}).json()["access_token"]
    res = client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403

def test_admin_full_access(client):
    token = client.post("/api/auth/token", json={"username_or_email": "admin_user", "password": "pass123"}).json()["access_token"]
    res = client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert len(res.json()) >= 5

def test_forgot_password_and_reset(client):
    req_res = client.post("/api/auth/forgot-password", json={"email_or_username": "customer_user"})
    assert req_res.status_code == 200
    code = req_res.json()["demo_reset_code"]

    reset_res = client.post("/api/auth/reset-password", json={"token_or_username": code, "new_password": "newpass123"})
    assert reset_res.status_code == 200

    login_res = client.post("/api/auth/token", json={"username_or_email": "customer_user", "password": "newpass123"})
    assert login_res.status_code == 200
