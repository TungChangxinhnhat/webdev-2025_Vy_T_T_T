# owner_checks.py
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models import News, Comment, User

def _cu():  # current user
    from auth_protect import get_current_user
    return Depends(get_current_user)

def owner_or_admin_news(news_id: int, db: Session = Depends(get_db), current: User = _cu()):
    news = db.get(News, news_id)
    if not news: raise HTTPException(404, "News not found")
    if current.is_admin or news.author_id == current.id:
        return news
    raise HTTPException(403, "Not owner")

def owner_or_admin_comment(comment_id: int, db: Session = Depends(get_db), current: User = _cu()):
    c = db.get(Comment, comment_id)
    if not c: raise HTTPException(404, "Comment not found")
    if current.is_admin or c.author_id == current.id:
        return c
    raise HTTPException(403, "Not owner")
