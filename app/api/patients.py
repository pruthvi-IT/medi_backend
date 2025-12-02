# app/api/patients.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.deps import get_db, dev_auth

# Main router for /v1/... endpoints
router = APIRouter(prefix="/v1", tags=["patients"], dependencies=[Depends(dev_auth)])

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
    patient = models.Patient(
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


@router.get(
    "/patient-details/{patientId}",
    summary="Get basic details for a patient by id",
)
def get_patient_details(
    patientId: int,
    db: Session = Depends(get_db),
):
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


@router.get(
    "/fetch-session-by-patient/{patientId}",
    summary="Get all sessions for a given patient id",
)
def get_sessions_by_patient(
    patientId: int,
    db: Session = Depends(get_db),
):
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


@router.get(
    "/all-session",
    summary="Get all sessions for a given userId",
)
def get_all_sessions(
    userId: str = Query(..., description="External user id"),
    db: Session = Depends(get_db),
):
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
