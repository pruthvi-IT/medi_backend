import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def gen_id(prefix=""):
    return f"{prefix}{uuid.uuid4().hex}"

class Patient(Base):
    __tablename__ = "patients"
    id = Column(String, primary_key=True, default=lambda: gen_id("patient_"))
    name = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    pronouns = Column(String, nullable=True)

class Session(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, default=lambda: gen_id("session_"))
    user_id = Column(String, nullable=False)
    patient_id = Column(String, nullable=False)
    status = Column(String, default="recording")
    start_time = Column(TIMESTAMP(timezone=False), nullable=True)
    end_time = Column(TIMESTAMP(timezone=False), nullable=True)
    total_chunks_client = Column(Integer, default=0)
    created_at = Column(TIMESTAMP(timezone=False), default=datetime.utcnow)

class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    chunk_number = Column(Integer, nullable=False)
    gcs_path = Column(String, nullable=False)
    uploaded = Column(Boolean, default=False)
    public_url = Column(String, nullable=True)
    mime_type = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=False), default=datetime.utcnow)
    session = relationship("Session", backref="chunks")
