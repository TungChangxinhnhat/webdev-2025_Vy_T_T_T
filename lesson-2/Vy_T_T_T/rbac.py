# rbac.py
from fastapi import Depends, HTTPException
from models import User

def _resolve_current_user():
    from auth_protect import get_current_user
    return Depends(get_current_user)

def require_verified_author_or_admin(current: User = _resolve_current_user()):
    if current.is_admin or current.is_author_verified:
        return current
    raise HTTPException(403, "Author verification required")
