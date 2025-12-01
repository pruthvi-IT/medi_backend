# app/db.py
import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from app import models
from dotenv import load_dotenv

load_dotenv()

# Prefer DATABASE_URL if provided (Railway, Heroku style)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DB_USER = os.getenv("POSTGRES_USER", "medi")
    DB_PASS = os.getenv("POSTGRES_PASSWORD", "medi_pwd")
    DB_HOST = os.getenv("POSTGRES_HOST", "db")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME = os.getenv("POSTGRES_DB", "medi")
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# If using SQLite fallback for local convenience, check for sqlite URL
# (Set DATABASE_URL=sqlite:///./medi.db to use file DB)
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
metadata = MetaData()


def init_db():
    models.Base.metadata.create_all(bind=engine)
