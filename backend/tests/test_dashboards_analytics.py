"""
Tests for Dashboards & Analytics Layer
backend/tests/test_dashboards_analytics.py
"""
import pytest
from fastapi.testclient import TestClient
from backend.security.jwt_auth import create_access_token
from backend.src.main import app

client = TestClient(app)


def get_auth_header(username: str = "customer@example.com", role: str = "Customer"):
    token = create_access_token({"sub": username, "role": role, "full_name": "Test User"})
    return {"Authorization": f"Bearer {token}"}


class TestCustomerDashboardRestrictedView:

    def test_customer_can_fetch_own_complaints_customer_view(self):
        headers = get_auth_header("cust_dash@nexalink.com", "Customer")
        
        create_res = client.post("/complaints", headers=headers, json={
            "customer_email": "cust_dash@nexalink.com",
            "customer_name": "Customer Dash User",
            "title": "Internet Slow Speed Issue",
            "category": "Network Outages & Fiber Disconnection",
            "description": "Fiber internet speed dropped from 100Mbps to 2Mbps."
        })
        assert create_res.status_code == 201
        cid = create_res.json()["id"]

        res = client.get(f"/complaints/{cid}/customer-view", headers=headers)
        assert res.status_code == 200
        data = res.json()

        assert "complaint_number" in data
        assert "status" in data
        assert "professional_response" in data
        assert "status_timeline" in data
        assert "repeat_complaint_chain" in data

        assert "agent_guidance" not in data
        assert "verification_score" not in data
        assert "python_validation_passed" not in data
        assert "genai_analysis_result" not in data
        assert "security_flags" not in data

    def test_customer_cannot_access_other_customer_view_returns_403(self):
        headers_cust1 = get_auth_header("customer1@nexalink.com", "Customer")
        headers_cust2 = get_auth_header("customer2@nexalink.com", "Customer")

        create_res = client.post("/complaints", headers=headers_cust1, json={
            "customer_email": "customer1@nexalink.com",
            "customer_name": "Customer One",
            "title": "Private Billing Complaint",
            "category": "Billing & Overcharging",
            "description": "Unexplained surcharge on account bill."
        })
        assert create_res.status_code == 201
        cid = create_res.json()["id"]

        res = client.get(f"/complaints/{cid}/customer-view", headers=headers_cust2)
        assert res.status_code == 403
        assert "Forbidden" in res.json()["detail"]

    def test_my_complaints_endpoint(self):
        headers = get_auth_header("my_cust@nexalink.com", "Customer")
        res = client.get("/complaints/my", headers=headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)


class TestAdminAnalyticsAndTrends:

    def test_admin_kpis_endpoint(self):
        headers = get_auth_header("admin@nexalink.com", "Admin")
        res = client.get("/admin/analytics/kpis", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "total_complaints" in data
        assert "open_complaints" in data
        assert "resolved_complaints" in data
        assert "mismatch_rate" in data
        assert "manual_review_queue_size" in data

    def test_category_trends_endpoint(self):
        headers = get_auth_header("admin@nexalink.com", "Admin")
        res = client.get("/admin/analytics/trends", headers=headers)
        assert res.status_code == 200
        trends = res.json()
        assert isinstance(trends, list)
        for t in trends:
            assert "category" in t
            assert "recent_count" in t
            assert "previous_count" in t
            assert "percentage_change" in t
            assert "is_rising" in t
            assert "trend_label" in t

    def test_report_export_csv(self):
        headers = get_auth_header("admin@nexalink.com", "Admin")
        res = client.get("/admin/reports/export/complaint_analysis?format=csv", headers=headers)
        assert res.status_code == 200
        assert "text/csv" in res.headers["content-type"]
        assert "Complaint ID" in res.text

    def test_report_export_excel(self):
        headers = get_auth_header("admin@nexalink.com", "Admin")
        res = client.get("/admin/reports/export/department_performance?format=excel", headers=headers)
        assert res.status_code == 200
        assert "application/vnd.ms-excel" in res.headers["content-type"]

    def test_report_export_pdf(self):
        headers = get_auth_header("admin@nexalink.com", "Admin")
        res = client.get("/admin/reports/export/summary?format=pdf", headers=headers)
        assert res.status_code == 200
        assert "application/pdf" in res.headers["content-type"]
        assert res.content.startswith(b"%PDF")
