# app/api/templates.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.deps import get_db, dev_auth
from app import models, schemas

router = APIRouter(prefix="/v1", tags=["templates"])

@router.get("/fetch-default-template-ext", response_model=List[schemas.TemplateOut], dependencies=[Depends(dev_auth)])
def get_user_templates(userId: str = Query(...), db: Session = Depends(get_db)):
    # For simplicity: return all templates where user_id == userId OR user_id is null (defaults)
    templates = (
        db.query(models.Template)
        .filter((models.Template.user_id == userId) | (models.Template.user_id == None))  # noqa: E711
        .all()
    )
    if not templates:
        # seed one default if empty
        default = models.Template(template_id="new_patient_visit", name="New Patient Visit", user_id=None)
        db.add(default)
        db.commit()
        db.refresh(default)
        templates = [default]

    return [
        schemas.TemplateOut(templateId=t.template_id, name=t.name)
        for t in templates
    ]
