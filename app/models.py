# app/models.py
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, index=True)  # optional mapping to client id
    user_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Session(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, index=True)  # e.g. "session_123"
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    user_id = Column(String, index=True, nullable=False)
    patient_name = Column(String, nullable=False)
    status = Column(String, default="recording")
    start_time = Column(DateTime(timezone=True))
    template_id = Column(String, nullable=True)

class AudioChunk(Base):
    __tablename__ = "audio_chunks"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    chunk_number = Column(Integer, nullable=False)
    gcs_path = Column(String, nullable=False)
    public_url = Column(String, nullable=True)
    mime_type = Column(String, nullable=True)
    is_last = Column(Boolean, default=False)
    total_chunks_client = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Template(Base):
    __tablename__ = "templates"
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    user_id = Column(String, index=True, nullable=True)  # null = default/global
