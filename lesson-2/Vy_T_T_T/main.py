# main.py
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from db import Base, engine

app = FastAPI(title="LMS 2.0 Auth Demo")

app.add_middleware(SessionMiddleware, secret_key="change_me")

from auth_local import router as local_auth_router
try:
    from auth_github import router as gh_router
    HAVE_GITHUB = True
except Exception:
    HAVE_GITHUB = False

from news_router import router as news_router
from comments_router import router as comments_router

app.include_router(local_auth_router)
if HAVE_GITHUB:
    app.include_router(gh_router)
app.include_router(news_router)
app.include_router(comments_router)

@app.get("/health")
def health():
    return {"ok": True}

import models  # noqa: F401
Base.metadata.create_all(engine)
