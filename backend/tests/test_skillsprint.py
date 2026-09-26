import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_skillsprint_employees_list():
    response = client.get("/api/skillsprint/employees")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_skillsprint_create_employee():
    payload = {
        "full_name": "Test Employee",
        "email": "test.employee@novacart.com",
        "department": "Engineering",
        "role_title": "Software Engineer",
        "seniority_level": "Mid",
        "prior_experience_years": 2.5,
        "current_skills": ["Python", "FastAPI", "React"]
    }
    response = client.post("/api/skillsprint/employees", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Test Employee"
    assert data["department"] == "Engineering"

def test_skillsprint_role_matrices():
    response = client.get("/api/skillsprint/roles")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_skillsprint_onboarding_generation():
    # First fetch or create employee
    emp_res = client.get("/api/skillsprint/employees")
    assert emp_res.status_code == 200
    employees = emp_res.json()
    
    if len(employees) > 0:
        emp_id = employees[0]["id"]
    else:
        # Create one
        create_res = client.post("/api/skillsprint/employees", json={
            "full_name": "Onboarding Test User",
            "email": "onboarding.test@novacart.com",
            "department": "Customer Service",
            "role_title": "Customer Support Specialist"
        })
        emp_id = create_res.json()["id"]

    # Generate plan
    gen_res = client.post("/api/skillsprint/onboarding/generate", json={
        "employee_id": emp_id,
        "role_code": "ROLE-ENG-01"
    })
    assert gen_res.status_code == 200
    plan_data = gen_res.json()
    assert "learning_modules" in plan_data
    assert "verification_status" in plan_data
    assert plan_data["coverage_score"] >= 0.0
