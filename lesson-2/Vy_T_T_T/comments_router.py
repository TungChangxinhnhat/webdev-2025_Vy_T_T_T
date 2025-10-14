# comments_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db
from models import Comment, News, User
from auth_protect import get_current_user
from owner_checks import owner_or_admin_comment

router = APIRouter(
    prefix="/comments",
    tags=["comments"],
    dependencies=[Depends(get_current_user)],  # đóng toàn bộ bằng Bearer
)

@router.post("", response_model=dict)
def create_comment(
    payload: dict,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    news_id = payload.get("news_id")
    body = payload.get("body")
    if not news_id or not body:
        raise HTTPException(422, "news_id & body required")
    if not db.get(News, news_id):
        raise HTTPException(404, "News not found")
    c = Comment(news_id=news_id, body=body, author_id=current.id)
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"id": c.id}

@router.put("/{comment_id}", response_model=dict)
def update_comment(
    comment: Comment = Depends(owner_or_admin_comment),
    payload: dict | None = None,
    db: Session = Depends(get_db),
):
    payload = payload or {}
    if "body" in payload:
        comment.body = payload["body"]
    db.commit()
    return {"ok": True}

@router.delete("/{comment_id}", response_model=dict)
def delete_comment(
    comment: Comment = Depends(owner_or_admin_comment),
    db: Session = Depends(get_db),
):
    db.delete(comment)
    db.commit()
    return {"ok": True}
