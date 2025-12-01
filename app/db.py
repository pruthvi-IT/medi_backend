# app/db.py
import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger("uvicorn.error")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # fallback to sqlite for debug/dev only
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./medi.db")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
metadata = MetaData()

def init_db():
    # Import models so they are registered with SQLAlchemy Base
    try:
        from app import models  # noqa: WPS433
    except Exception:
        logger.warning("No models module found or failed to import models.")
    # Create tables (idempotent)
    try:
        if hasattr(models, "Base"):
            models.Base.metadata.create_all(bind=engine)
        else:
            logger.warning("No Base in models; skipping create_all.")
    except Exception as e:
        logger.exception("Error creating DB tables: %s", e)
        raise
