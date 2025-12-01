# app/main.py
import logging
from fastapi import FastAPI
from app.db import init_db
from app.api.upload_routes import router as upload_router

logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="MediNote API")

app.include_router(upload_router)

@app.on_event("startup")
def on_startup():
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.exception("Database initialization failed at startup. Continuing. Error: %s", e)

@app.get("/")
def root():
    return {"status": "ok"}
