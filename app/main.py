# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db

# If these modules exist, keep these imports.
# If you do NOT have templates.py, comment out that line + include_router line below.
from app.api import patients as patients_api
from app.api import recordings as recordings_api
from app.api import templates as templates_api  # comment if you don't have this file


# THIS is what uvicorn is looking for: a top-level variable named "app"
app = FastAPI(title="Medi Backend")


# CORS – keep open for now
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health():
    return {"status": "ok"}


@app.on_event("startup")
def on_startup():
    # Initialize DB (create tables if not present)
    init_db()


# Include routers – these define the /v1/... endpoints
app.include_router(patients_api.router)
app.include_router(patients_api.user_router)
app.include_router(templates_api.router)   
app.include_router(recordings_api.router)

