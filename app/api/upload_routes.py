# app/api/upload_routes.py
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from app import db as _db
from app.storage import create_signed_upload_url
import logging
import os

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/v1")

# Basic auth dependency using DEV_AUTH_TOKEN for dev testing
def dev_auth(authorization: str | None = Header(default=None)):
    dev_token = os.getenv("DEV_AUTH_TOKEN")
    if not dev_token:
        return True
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    token = authorization.split(" ", 1)[1]
    if token != dev_token:
        raise HTTPException(status_code=403, detail="Invalid token")
    return True

class PresignRequest(BaseModel):
    sessionId: str
    chunkNumber: int
    mimeType: str = "audio/wav"

@router.post("/get-presigned-url")
def get_presigned_url(body: PresignRequest, _auth=Depends(dev_auth)):
    key = f"sessions/{body.sessionId}/chunk_{body.chunkNumber}.wav"
    try:
        res = create_signed_upload_url(key, expires_in=3600)
        return {
            "url": res["signed_url"],
            "gcsPath": res["path"],
            "publicUrl": res["public_url"]
        }
    except Exception as e:
        logger.exception("Failed to create presigned upload URL")
        raise HTTPException(status_code=500, detail=str(e))

class NotifyRequest(BaseModel):
    sessionId: str
    gcsPath: str
    chunkNumber: int
    isLast: bool = False
    totalChunksClient: int = 0
    publicUrl: str | None = None
    mimeType: str = "audio/wav"

@router.post("/notify-chunk-uploaded")
def notify_chunk_uploaded(body: NotifyRequest, _auth=Depends(dev_auth)):
    # Implement DB logic here: create chunk record / mark uploaded etc.
    # Minimal implementation: log and return success.
    logger.info("Chunk uploaded: session=%s chunk=%s path=%s publicUrl=%s", body.sessionId, body.chunkNumber, body.gcsPath, body.publicUrl)
    # You should insert DB record into your chunks table here.
    return {"success": True}
