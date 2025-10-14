# auth_protect.py
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
import jwt, os
from db import get_db
from models import User

SECRET = os.getenv("JWT_SECRET", "dev_secret_change_me")

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    auth = request.headers.get("authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(401, "Missing bearer token")
    token = auth.split()[1]
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
    except Exception:
        raise HTTPException(401, "Invalid token")
    uid = payload.get("sub")
    user = db.get(User, int(uid)) if uid else None
    if not user:
        raise HTTPException(401, "User not found")
    return user
