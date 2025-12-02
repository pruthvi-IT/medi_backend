# app/deps.py
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.config import DEV_AUTH_TOKEN

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def dev_auth(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    token = authorization.split(" ", 1)[1]
    if token != DEV_AUTH_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")
    return True
