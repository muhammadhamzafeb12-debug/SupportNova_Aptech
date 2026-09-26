"""
Backend Security & Authentication Module
Decoupled authentication logic supporting bcrypt with standard library fallback.
"""
import hashlib
import hmac
from typing import Optional, Dict, Any

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

def hash_password_fallback(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against hash."""
    try:
        if HAS_BCRYPT and hashed_password.startswith("$2b$"):
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        else:
            return hmac.compare_digest(hash_password_fallback(plain_password), hashed_password)
    except Exception:
        return False

def get_hash(password: str) -> str:
    if HAS_BCRYPT:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    return hash_password_fallback(password)

# Mock user database for development/scaffolding
MOCK_USERS = {
    "customer@velvocart.com": {
        "username": "customer@velvocart.com",
        "full_name": "Sarah Jenkins",
        "role": "Customer",
        "password_hash": get_hash("password123")
    },
    "agent@velvocart.com": {
        "username": "agent@velvocart.com",
        "full_name": "Marcus Vance",
        "role": "Agent",
        "password_hash": get_hash("password123")
    },
    "reviewer@velvocart.com": {
        "username": "reviewer@velvocart.com",
        "full_name": "Elena Rostova",
        "role": "Reviewer",
        "password_hash": get_hash("password123")
    },
    "manager@velvocart.com": {
        "username": "manager@velvocart.com",
        "full_name": "David Sterling",
        "role": "Manager",
        "password_hash": get_hash("password123")
    },
    "admin@velvocart.com": {
        "username": "admin@velvocart.com",
        "full_name": "System Administrator",
        "role": "Admin",
        "password_hash": get_hash("password123")
    },
    # Aliases for compatibility
    "customer@nexalink.com": {
        "username": "customer@nexalink.com",
        "full_name": "Sarah Jenkins",
        "role": "Customer",
        "password_hash": get_hash("password123")
    },
    "admin@nexalink.com": {
        "username": "admin@nexalink.com",
        "full_name": "System Administrator",
        "role": "Admin",
        "password_hash": get_hash("password123")
    }
}

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticates user credentials and returns user dict if valid."""
    user = MOCK_USERS.get(username.lower().strip())
    if not user:
        return None
    if verify_password(password, user["password_hash"]):
        return {
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"]
        }
    return None

def get_available_roles():
    """Returns list of system roles."""
    return ["Customer", "Agent", "Reviewer", "Manager", "Admin"]
