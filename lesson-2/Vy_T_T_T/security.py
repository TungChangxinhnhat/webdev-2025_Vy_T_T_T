# security.py
from __future__ import annotations
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict

import jwt
from argon2 import PasswordHasher

from dotenv import load_dotenv

load_dotenv()

# ---- config ----
JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret_change_me")
JWT_ALG = "HS256"
JWT_ACCESS_MINUTES = int(os.getenv("JWT_ACCESS_MINUTES", "15"))
JWT_REFRESH_DAYS = int(os.getenv("JWT_REFRESH_DAYS", "30"))

# ---- password hashing (Argon2) ----
_ph = PasswordHasher()

def hash_password(plain: str) -> str:
    return _ph.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, plain)
    except Exception:
        return False

# ---- access token (JWT) ----
def create_access_token(sub: str, extra_claims: Dict[str, Any] | None = None) -> str:
    now = datetime.utcnow()
    payload: Dict[str, Any] = {
        "sub": sub,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_ACCESS_MINUTES)).timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

# ---- refresh token (opaque) ----
def create_refresh_token() -> str:
    # 32 bytes ngẫu nhiên → 64 hex chars
    return secrets.token_hex(32)

def hash_refresh_token(token: str) -> str:
    # Lưu SHA-256 hex (64 ký tự) vào DB để tránh lộ token gốc
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def refresh_expiry_utc() -> datetime:
    return datetime.utcnow() + timedelta(days=JWT_REFRESH_DAYS)
