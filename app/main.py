import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import sessions, patients
from app.db import init_db

app = FastAPI(title="MediNote API (FastAPI)")

# CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router, prefix="/v1", tags=["sessions"])
app.include_router(patients.router, prefix="/v1", tags=["patients"])

@app.on_event("startup")
def on_startup():
    init_db()
