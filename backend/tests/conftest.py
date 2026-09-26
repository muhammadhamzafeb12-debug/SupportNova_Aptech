import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database import Base, get_db
from backend.auth.auth import get_password_hash
from backend.models import User, UserRole
from backend.database_seed import seed_database

TEST_DB_FILE = "./test_runner_unified.db"
SQLALCHEMY_TEST_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"

engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def init_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    # Seed default base dataset
    seed_database(db=db)
    
    # Seed test-specific accounts for authentication test suite
    auth_test_users = [
        ("admin_user", "admin_test@novacart.com", "Admin Test", "pass123", UserRole.ADMIN.value, True),
        ("manager_user", "manager_test@novacart.com", "Manager Test", "pass123", UserRole.MANAGER.value, True),
        ("reviewer_user", "reviewer_test@novacart.com", "Reviewer Test", "pass123", UserRole.REVIEWER.value, True),
        ("agent_user", "agent_test@novacart.com", "Agent Test", "pass123", UserRole.AGENT.value, True),
        ("customer_user", "customer_test@gmail.com", "Customer Test", "pass123", UserRole.CUSTOMER.value, True),
        ("disabled_user", "disabled_test@novacart.com", "Disabled Test", "pass123", UserRole.CUSTOMER.value, False),
        ("testadmin", "testadmin@novacart.com", "Test Admin", "admin123", UserRole.ADMIN.value, True)
    ]
    for username, email, full_name, pwd, role, is_act in auth_test_users:
        if not db.query(User).filter(User.username == username).first():
            u = User(
                username=username,
                email=email,
                full_name=full_name,
                hashed_password=get_password_hash(pwd),
                role=role,
                is_active=is_act
            )
            db.add(u)
    db.commit()
    db.close()
    yield

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
