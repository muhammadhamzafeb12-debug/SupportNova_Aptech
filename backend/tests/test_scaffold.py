"""
Basic scaffolding test to verify backend imports and configuration integrity.
"""
from backend.config_loader import load_organization_config, load_categories_config, load_departments_config
from backend.security.auth import authenticate_user

def test_config_loader():
    org = load_organization_config()
    cats = load_categories_config()
    depts = load_departments_config()
    
    assert "VelvoCart" in org.get("organization", {}).get("name")
    assert len(cats.get("categories", [])) == 10
    assert len(depts.get("departments", [])) == 9

def test_auth_scaffold():
    user = authenticate_user("admin@velvocart.com", "password123")
    assert user is not None
    assert user["role"] == "Admin"
