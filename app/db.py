# app/db.py
from sqlalchemy import create_engine, text
from sqlalchemy import inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.config import DATABASE_URL
import logging

logger = logging.getLogger("uvicorn.error")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args,
    poolclass=None if not DATABASE_URL.startswith("sqlite") else NullPool,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    from app import models  # noqa
    try:
        models.Base.metadata.create_all(bind=engine)
        logger.info("Database tables created / verified successfully.")
        try:
            _ensure_schema()
        except Exception as e:
            logger.warning("Schema ensure step failed: %s", e)
    except Exception as e:
        logger.exception("Error creating DB tables: %s", e)
        raise


def _ensure_schema():
    inspector = inspect(engine)
    try:
        cols = [c.get("name") for c in inspector.get_columns("patients")]
    except Exception:
        cols = []
    if cols is not None and "created_at" not in cols:
        logger.info("Adding missing column patients.created_at")
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE patients ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW()"))
        logger.info("Added patients.created_at successfully")
