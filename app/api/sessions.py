from fastapi import APIRouter, Depends, HTTPException, Header
from datetime import datetime
from typing import Optional
from app.db import SessionLocal
from app.models import Session, Chunk
from app.schemas import CreateSessionReq, CreateSessionResp, PresignedReq, PresignedResp, NotifyChunkReq
from app import utils
from sqlalchemy.orm import Session as DbSession

router = APIRouter()

def require_auth(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing auth")
    # Accept any bearer token in dev mode
    return authorization

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload-session", response_model=CreateSessionResp, status_code=201)
def create_session(payload: CreateSessionReq, auth: str = Depends(require_auth), db: DbSession = Depends(get_db)):
    s = Session(
        user_id=payload.userId,
        patient_id=payload.patientId,
        status=payload.status or "recording",
        start_time=datetime.fromisoformat(payload.startTime) if payload.startTime else None
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return {"id": s.id}

@router.post("/get-presigned-url", response_model=PresignedResp)
def get_presigned(payload: PresignedReq, auth: str = Depends(require_auth), db: DbSession = Depends(get_db)):
    # ensure session exists
    sess = db.query(Session).filter(Session.id == payload.sessionId).first()
    if not sess:
        raise HTTPException(status_code=404, detail="session not found")

    key = f"sessions/{payload.sessionId}/chunk_{payload.chunkNumber}.wav"
    url, public_url = utils.generate_presigned_put_url(key, content_type=payload.mimeType)
    # save chunk record (uploaded=False until notify) - we create an entry so it's known
    chunk = Chunk(session_id=payload.sessionId, chunk_number=payload.chunkNumber, gcs_path=key, uploaded=False, mime_type=payload.mimeType)
    db.add(chunk)
    db.commit()
    db.refresh(chunk)
    return {"url": url, "gcsPath": key, "publicUrl": public_url}

@router.post("/notify-chunk-uploaded")
def notify_chunk(payload: NotifyChunkReq, auth: str = Depends(require_auth), db: DbSession = Depends(get_db)):
    # Validate session
    sess = db.query(Session).filter(Session.id == payload.sessionId).first()
    if not sess:
        raise HTTPException(status_code=404, detail="session not found")
    # mark chunk uploaded
    chunk = db.query(Chunk).filter(Chunk.session_id == payload.sessionId, Chunk.chunk_number == payload.chunkNumber).first()
    if not chunk:
        # If chunk wasn't created earlier, create it now
        chunk = Chunk(session_id=payload.sessionId, chunk_number=payload.chunkNumber, gcs_path=payload.gcsPath, uploaded=True, public_url=payload.publicUrl, mime_type=payload.mimeType)
        db.add(chunk)
    else:
        chunk.uploaded = True
        chunk.public_url = payload.publicUrl
        chunk.mime_type = payload.mimeType
    # update totalChunksClient if provided
    if payload.totalChunksClient:
        sess.total_chunks_client = payload.totalChunksClient
    if payload.isLast:
        sess.status = "completed"
        sess.end_time = datetime.utcnow()
    db.commit()
    return {}
