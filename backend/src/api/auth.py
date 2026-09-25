"""
Authentication API Router
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from backend.schemas.schemas import UserRegister, UserLogin, TokenResponse, TokenRefreshRequest, UserProfile
from backend.security.rate_limiter import rate_limit_login
from backend.security.auth import verify_password, get_hash
from backend.security.jwt_auth import (
    USER_DB,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
def register_user(payload: UserRegister):
    email_clean = payload.email.lower().strip()
    if email_clean in USER_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address already registered"
        )
    
    user_entry = {
        "username": email_clean,
        "full_name": payload.full_name,
        "role": payload.role or "Customer",
        "password_hash": get_hash(payload.password)
    }
    USER_DB[email_clean] = user_entry

    user_payload = {
        "sub": email_clean,
        "full_name": payload.full_name,
        "role": user_entry["role"]
    }
    access_token = create_access_token(user_payload)
    refresh_token = create_refresh_token({"sub": email_clean})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "username": email_clean,
            "email": email_clean,
            "full_name": payload.full_name,
            "role": user_entry["role"]
        }
    }

@router.post("/login", response_model=TokenResponse)
def login_user(payload: UserLogin, request: Request, _rl: None = Depends(rate_limit_login)):
    username_clean = payload.username.lower().strip()
    user = USER_DB.get(username_clean)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    user_payload = {
        "sub": user["username"],
        "full_name": user["full_name"],
        "role": user["role"]
    }
    access_token = create_access_token(user_payload)
    refresh_token = create_refresh_token({"sub": user["username"]})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "username": user["username"],
            "email": user["username"],
            "full_name": user["full_name"],
            "role": user["role"]
        }
    }

@router.post("/refresh")
def refresh_token(payload: TokenRefreshRequest):
    decoded = decode_token(payload.refresh_token)
    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Invalid token type")
    username = decoded.get("sub")
    user = USER_DB.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    access_token = create_access_token({
        "sub": user["username"],
        "full_name": user["full_name"],
        "role": user["role"]
    })
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserProfile)
def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "email": current_user["username"],
        "full_name": current_user["full_name"],
        "role": current_user["role"]
    }
