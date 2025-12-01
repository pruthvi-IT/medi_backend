from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
from app.db import SessionLocal
from app.models import Patient, Session as Sess
from app.schemas import PatientCreateReq
from sqlalchemy.orm import Session

router = APIRouter()

# Minimal auth mock
def require_auth(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing auth")
    # dev mode: accept any bearer token or specific test token
    return authorization

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/patients")
def get_patients(userId: str, auth: str = Depends(require_auth), db: Session = Depends(get_db)):
    patients = db.query(Patient).filter(Patient.user_id == userId).all()
    return {"patients": [{"id": p.id, "name": p.name} for p in patients]}

@router.post("/add-patient-ext", status_code=201)
def create_patient(payload: PatientCreateReq, auth: str = Depends(require_auth), db: Session = Depends(get_db)):
    p = Patient(name=payload.name, user_id=payload.userId)
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"patient": {"id": p.id, "name": p.name, "user_id": p.user_id, "pronouns": p.pronouns}}

@router.get("/fetch-session-by-patient/{patientId}")
def get_sessions_by_patient(patientId: str, auth: str = Depends(require_auth), db: Session = Depends(get_db)):
    sessions = db.query(Sess).filter(Sess.patient_id == patientId).all()
    out = []
    for s in sessions:
        out.append({
            "id": s.id,
            "date": s.start_time.isoformat() if s.start_time else None,
            "session_title": None,
            "session_summary": None,
            "start_time": s.start_time.isoformat() if s.start_time else None
        })
    return {"sessions": out}
