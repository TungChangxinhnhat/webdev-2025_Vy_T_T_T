# news_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db
from models import News, User
from auth_protect import get_current_user
from rbac import require_verified_author_or_admin
from owner_checks import owner_or_admin_news

router = APIRouter(prefix="/news", tags=["news"], dependencies=[Depends(get_current_user)])

@router.get("", response_model=list[dict])
def list_news(db: Session = Depends(get_db)):
    rows = db.query(News).order_by(News.created_at.desc()).limit(50).all()
    return [{"id": r.id, "title": r.title, "author_id": r.author_id, "created_at": r.created_at} for r in rows]

@router.post("", response_model=dict)
def create_news(
    payload: dict,
    db: Session = Depends(get_db),
    current: User = Depends(require_verified_author_or_admin),
):
    title = payload.get("title")
    body = payload.get("body")
    if not title or not body:
        raise HTTPException(422, "title & body required")
    n = News(title=title, body=body, author_id=current.id)
    db.add(n)
    db.commit()
    db.refresh(n)
    return {"id": n.id}

@router.put("/{news_id}", response_model=dict)
def update_news(
    news: News = Depends(owner_or_admin_news),
    payload: dict | None = None,
    db: Session = Depends(get_db),
):
    payload = payload or {}
    if "title" in payload:
        news.title = payload["title"]
    if "body" in payload:
        news.body = payload["body"]
    db.commit()
    return {"ok": True}

@router.delete("/{news_id}", response_model=dict)
def delete_news(
    news: News = Depends(owner_or_admin_news),
    db: Session = Depends(get_db),
):
    db.delete(news)
    db.commit()
    return {"ok": True}
