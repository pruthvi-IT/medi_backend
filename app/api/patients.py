# app/api/patients.py

from typing import List
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db import engine

from app import models, schemas
from app.deps import get_db, dev_auth

# Main router for /v1/... endpoints
router = APIRouter(prefix="/v1", tags=["patients"], dependencies=[Depends(dev_auth)])
logger = logging.getLogger("uvicorn.error")

# Separate router for the weird user endpoint from Postman: /users/asd3fd2faec
user_router = APIRouter(tags=["users"], dependencies=[Depends(dev_auth)])


# ---------------------------------------------------------------------------
# PATIENT ENDPOINTS
# ---------------------------------------------------------------------------

@router.post(
    "/patients",
    response_model=List[schemas.PatientOut],
    summary="List patients for a given userId",
)
def list_patients(
    userId: str = Query(..., description="External user id (e.g. auth user)"),
    db: Session = Depends(get_db),
):
    """
    Return all patients that belong to the given `userId`.

    This matches the Postman behavior where `/v1/patients` is used
    to fetch a list, even though it's a POST.
    """
    try:
        patients = (
            db.query(models.Patient)
            .filter(models.Patient.user_id == userId)
            .order_by(models.Patient.id.desc())
            .all()
        )
        return [
            schemas.PatientOut(
                id=p.id,
                name=p.name,
                userId=p.user_id,
            )
            for p in patients
        ]
    except Exception as e:
        logger.exception("list_patients failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/add-patient-ext",
    response_model=schemas.PatientOut,
    summary="Create a new patient for a given userId",
)
def create_patient(
    body: schemas.PatientCreate,
    db: Session = Depends(get_db),
):
    """
    Create a patient.

    Expected body (schemas.PatientCreate):

    {
      "name": "...",
      "userId": "..."
    }
    """
    try:
        next_id = None
        try:
            id_default = db.execute(text("SELECT column_default FROM information_schema.columns WHERE table_name='patients' AND column_name='id'")).scalar()
        except Exception:
            id_default = None
        if not id_default:
            try:
                db.execute(text("CREATE SEQUENCE IF NOT EXISTS patients_id_seq"))
                db.execute(text("SELECT setval('patients_id_seq'::regclass, COALESCE((SELECT MAX(id) FROM patients), 0)::bigint)"))
                next_id = db.execute(text("SELECT nextval('patients_id_seq'::regclass)")).scalar()
            except Exception:
                next_id = None

        patient = models.Patient(
            id=next_id,
            name=body.name,
            user_id=body.userId,
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)
        return schemas.PatientOut(
            id=patient.id,
            name=patient.name,
            userId=patient.user_id,
        )
    except Exception as e:
        logger.exception("create_patient failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/patient-details/{patientId}",
    summary="Get basic details for a patient by id",
)
def get_patient_details(
    patientId: int,
    db: Session = Depends(get_db),
):
    try:
        patient = (
            db.query(models.Patient)
            .filter(models.Patient.id == patientId)
            .first()
        )
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        return {
            "id": patient.id,
            "name": patient.name,
            "userId": patient.user_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_patient_details failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/fetch-session-by-patient/{patientId}",
    summary="Get all sessions for a given patient id",
)
def get_sessions_by_patient(
    patientId: int,
    db: Session = Depends(get_db),
):
    try:
        sessions = (
            db.query(models.Session)
            .filter(models.Session.patient_id == patientId)
            .order_by(models.Session.start_time.desc())
            .all()
        )
        return [
            {
                "id": s.id,
                "patientId": s.patient_id,
                "userId": s.user_id,
                "patientName": s.patient_name,
                "status": s.status,
                "startTime": s.start_time,
                "templateId": s.template_id,
            }
            for s in sessions
        ]
    except Exception as e:
        logger.exception("get_sessions_by_patient failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/all-session",
    summary="Get all sessions for a given userId",
)
def get_all_sessions(
    userId: str = Query(..., description="External user id"),
    db: Session = Depends(get_db),
):
    try:
        sessions = (
            db.query(models.Session)
            .filter(models.Session.user_id == userId)
            .order_by(models.Session.start_time.desc())
            .all()
        )
        return [
            {
                "id": s.id,
                "patientId": s.patient_id,
                "userId": s.user_id,
                "patientName": s.patient_name,
                "status": s.status,
                "startTime": s.start_time,
                "templateId": s.template_id,
            }
            for s in sessions
        ]
    except Exception as e:
        logger.exception("get_all_sessions failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/admin/fix-patients-schema",
    summary="Fix patients schema",
)
def fix_patients_schema(_auth=Depends(dev_auth)):
    with engine.begin() as conn:
        id_type = None
        id_default = None
        created_exists = False
        try:
            t = conn.execute(text("SELECT data_type FROM information_schema.columns WHERE table_name='patients' AND column_name='id'"))
            id_type = t.scalar()
        except Exception:
            id_type = None
        try:
            d = conn.execute(text("SELECT column_default FROM information_schema.columns WHERE table_name='patients' AND column_name='id'"))
            id_default = d.scalar()
        except Exception:
            id_default = None
        try:
            c = conn.execute(text("SELECT 1 FROM information_schema.columns WHERE table_name='patients' AND column_name='created_at'"))
            created_exists = c.first() is not None
        except Exception:
            created_exists = False

        if not created_exists:
            conn.execute(text("ALTER TABLE patients ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW()"))

        if id_type and id_type not in ("integer", "bigint"):
            conn.execute(text("CREATE SEQUENCE IF NOT EXISTS patients_id_seq"))
            conn.execute(text("ALTER TABLE patients ALTER COLUMN id DROP NOT NULL"))
            conn.execute(text("ALTER TABLE patients ALTER COLUMN id TYPE INTEGER USING CASE WHEN (id ~ '^[0-9]+$') THEN id::integer ELSE NULL END"))
            conn.execute(text("UPDATE patients SET id = nextval('patients_id_seq') WHERE id IS NULL"))
            conn.execute(text("ALTER TABLE patients ALTER COLUMN id SET NOT NULL"))

        conn.execute(text("CREATE SEQUENCE IF NOT EXISTS patients_id_seq"))
        conn.execute(text("SELECT setval('patients_id_seq'::regclass, COALESCE((SELECT MAX(id) FROM patients), 0)::bigint)"))
        conn.execute(text("ALTER TABLE patients ALTER COLUMN id SET DEFAULT nextval('patients_id_seq'::regclass)"))

        try:
            def_row = conn.execute(text("SELECT column_default FROM information_schema.columns WHERE table_name='patients' AND column_name='id'"))
            id_default = def_row.scalar()
        except Exception:
            pass

        try:
            def_row2 = conn.execute(text("SELECT column_default, is_identity FROM information_schema.columns WHERE table_name='patients' AND column_name='id'"))
            id_default2, is_identity = def_row2.fetchone()
        except Exception:
            id_default2, is_identity = None, None
        if not id_default2 or (is_identity and str(is_identity).upper() != 'YES'):
            conn.execute(text("ALTER TABLE patients ALTER COLUMN id SET DEFAULT nextval('patients_id_seq'::regclass)"))

    return {"ok": True}


@router.get(
    "/admin/schema-status",
    summary="Schema status",
)
def schema_status(_auth=Depends(dev_auth)):
    with engine.begin() as conn:
        id_default = None
        created_default = None
        created_exists = False
        is_identity = None
        try:
            res = conn.execute(text("SELECT column_name, column_default, is_identity FROM information_schema.columns WHERE table_name='patients' AND column_name IN ('id','created_at')"))
            rows = res.fetchall()
            for r in rows:
                name = r[0]
                default = r[1]
                if name == "id":
                    id_default = default
                    is_identity = r[2]
                if name == "created_at":
                    created_exists = True
                    created_default = default
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    auto_inc = False
    if id_default:
        d = str(id_default).lower()
        auto_inc = ("nextval" in d)
    if is_identity and str(is_identity).upper() == 'YES':
        auto_inc = True
    return {
        "idDefault": id_default,
        "idAutoIncrement": auto_inc,
        "createdAtExists": created_exists,
        "createdAtDefault": created_default,
        "isIdentity": is_identity,
    }


# ---------------------------------------------------------------------------
# USER ENDPOINT (from Postman: /users/asd3fd2faec?email=...)
# ---------------------------------------------------------------------------

@user_router.get(
    "/users/asd3fd2faec",
    summary="Get or create user by email, return db id",
)
def get_user_db_id(
    email: str,
    db: Session = Depends(get_db),
):
    """
    Given an email, return the internal DB user id.

    If the user doesn't exist yet, it will be created.
    """
    user = (
        db.query(models.User)
        .filter(models.User.email == email)
        .first()
    )

    if not user:
        user = models.User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)

    return {"id": user.id, "email": user.email}
