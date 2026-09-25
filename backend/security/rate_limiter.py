"""
FastAPI Rate Limiter Module
Part C implementation for Phase 5 — Access Control & Data Security.
Applies IP and User-based rate limiting to prevent brute force and spam.
"""
import time
from typing import Dict, List
from fastapi import Request, HTTPException, status

# In-memory request timestamp tracking: { key: [timestamps] }
REQUEST_HISTORY: Dict[str, List[float]] = {}


def check_rate_limit(key: str, max_requests: int, window_seconds: int = 60):
    """
    Checks if a key (e.g., 'login:127.0.0.1' or 'complaints:user@example.com')
    has exceeded max_requests within window_seconds.
    """
    now = time.time()
    timestamps = REQUEST_HISTORY.get(key, [])
    
    # Filter timestamps within the current sliding window
    valid_timestamps = [t for t in timestamps if now - t < window_seconds]
    
    if len(valid_timestamps) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too Many Requests. Rate limit exceeded ({max_requests} requests per {window_seconds}s)."
        )
    
    valid_timestamps.append(now)
    REQUEST_HISTORY[key] = valid_timestamps


def rate_limit_login(request: Request):
    """Rate limit for POST /auth/login: 5 requests per minute per IP."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    key = f"login:{client_ip}"
    check_rate_limit(key, max_requests=5, window_seconds=60)


def rate_limit_complaints(request: Request):
    """Rate limit for POST /complaints: 10 requests per minute per IP/client."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    key = f"complaints:{client_ip}"
    check_rate_limit(key, max_requests=10, window_seconds=60)


def reset_rate_limits():
    """Utility function to clear rate limit state during testing."""
    REQUEST_HISTORY.clear()
