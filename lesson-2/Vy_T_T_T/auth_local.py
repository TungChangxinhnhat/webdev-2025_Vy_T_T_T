# auth_local.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime

from db import get_db
from models import User, RefreshSession
from schemas import RegisterIn, LoginIn, TokensOut, RefreshIn
from security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    hash_refresh_token, refresh_expiry_utc
)

router = APIRouter(prefix="/auth", tags=["auth"])

# --- helpers ---
def _client_fingerprint(req: Request):
    ua = req.headers.get("user-agent")
    ip = req.headers.get("x-forwarded-for", req.client.host if req.client else None)
    return ua, ip

# --- register ---
@router.post("/register", response_model=dict)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(400, "Email already exists")
    user = User(email=body.email, password_hash=hash_password(body.password))
    db.add(user); db.commit(); db.refresh(user)
    return {"id": user.id, "email": user.email}

# --- login ---
@router.post("/login", response_model=TokensOut)
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")

    access = create_access_token(str(user.id))
    refresh = create_refresh_token()

    ua, ip = _client_fingerprint(request)
    rs = RefreshSession(
        user_id=user.id,
        token_hash=hash_refresh_token(refresh),
        user_agent=ua, ip=ip,
        created_at=datetime.utcnow(),
        expires_at=refresh_expiry_utc()
    )
    db.add(rs); db.commit()
    return TokensOut(access_token=access, refresh_token=refresh)

@router.post("/refresh", response_model=dict)
def refresh(body: RefreshIn, db: Session = Depends(get_db)):
    h = hash_refresh_token(body.refresh_token)
    rs = db.query(RefreshSession).filter(
        RefreshSession.token_hash == h,
        RefreshSession.revoked_at.is_(None),
        RefreshSession.expires_at > datetime.utcnow()
    ).first()
    if not rs:
        raise HTTPException(401, "Invalid or expired refresh token")

    access = create_access_token(str(rs.user_id))
    return {"access_token": access, "token_type": "bearer"}

@router.post("/logout", response_model=dict)
def logout(body: RefreshIn, db: Session = Depends(get_db)):
    h = hash_refresh_token(body.refresh_token)
    rs = db.query(RefreshSession).filter(
        RefreshSession.token_hash == h, RefreshSession.revoked_at.is_(None)
    ).first()
    if not rs:
        raise HTTPException(404, "Session not found")
    rs.revoked_at = datetime.utcnow()
    db.commit()
    return {"ok": True}

@router.get("/sessions", response_model=list[dict])
def my_sessions(request: Request, db: Session = Depends(get_db)):
    from auth_protect import get_current_user  
    current = get_current_user(request, db)
    rows = db.query(RefreshSession).filter(
        RefreshSession.user_id == current.id,
        RefreshSession.revoked_at.is_(None),
        RefreshSession.expires_at > datetime.utcnow()
    ).order_by(RefreshSession.created_at.desc()).all()
    return [
        dict(id=r.id, user_agent=r.user_agent, ip=r.ip,
             created_at=r.created_at, expires_at=r.expires_at)
        for r in rows
    ]
