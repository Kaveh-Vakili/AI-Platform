"""FastAPI app entry point. Wires routers, DB, and the monitoring persistence hooks.

Run: uvicorn app.main:app --reload
"""
from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://stratos:stratos@localhost/stratos")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _wire_monitoring() -> None:
    from app.monitoring import persistence
    from app.models import HallucinationCheck, TokenUsageLog

    def write_token_log(**kw):
        with SessionLocal() as s:
            s.add(TokenUsageLog(**kw))
            s.commit()

    def write_hallucination_check(**kw):
        with SessionLocal() as s:
            s.add(HallucinationCheck(**kw))
            s.commit()

    persistence.write_token_log = write_token_log
    persistence.write_hallucination_check = write_hallucination_check


app = FastAPI(title="STRATOS AI", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["http://localhost:5173"],
    allow_methods=["*"], allow_headers=["*"], allow_credentials=True,
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    _wire_monitoring()
    import app.agents.core_agents  # noqa: F401
    import app.agents.control_agent  # noqa: F401


@app.get("/health")
def health():
    return {"status": "ok"}


from app.api.auth import router as auth_router
app.include_router(auth_router)