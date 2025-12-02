# app/db.py
from sqlalchemy import create_engine
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
    except Exception as e:
        logger.exception("Error creating DB tables: %s", e)
        raise
