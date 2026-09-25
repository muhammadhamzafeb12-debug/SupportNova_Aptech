"""
JWT Authentication & FastAPI Dependency Injection Module
"""
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from backend.security.auth import verify_password, get_hash, MOCK_USERS

SECRET_KEY = os.getenv("JWT_SECRET", "supportnova_super_secret_jwt_key_2026_prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer(auto_error=False)

# In-memory user store initialized with MOCK_USERS
USER_DB = dict(MOCK_USERS)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated - Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    payload = decode_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    user = USER_DB.get(username.lower().strip())
    if not user:
        # Fallback for dynamic users
        return {
            "username": username,
            "email": username,
            "full_name": payload.get("full_name", username),
            "role": payload.get("role", "Customer")
        }
    
    return {
        "username": user["username"],
        "email": user["username"],
        "full_name": user["full_name"],
        "role": user["role"]
    }

def require_role(*roles: str):
    """FastAPI Dependency enforcing role-based access control."""
    normalized_allowed_roles = [r.lower().strip() for r in roles]
    # Allow 'admin' / 'administrator' aliases
    if "admin" in normalized_allowed_roles and "administrator" not in normalized_allowed_roles:
        normalized_allowed_roles.append("administrator")
    if "administrator" in normalized_allowed_roles and "admin" not in normalized_allowed_roles:
        normalized_allowed_roles.append("admin")

    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_role = current_user.get("role", "").lower().strip()
        if user_role not in normalized_allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: User role '{current_user.get('role')}' does not have required permissions: {roles}"
            )
        return current_user

    return role_checker
