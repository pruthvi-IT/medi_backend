# app/api/recordings.py
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from sqlalchemy.orm import Session
from typing import Any
import os
import uuid
import logging

from app.deps import get_db, dev_auth
from app import models, schemas
from app.config import FILE_STORAGE_DIR
from app.supabase_storage import get_public_url, upload_file_from_path

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/v1", tags=["recordings"])

# Ensure storage dir exists
os.makedirs(FILE_STORAGE_DIR, exist_ok=True)


@router.post(
    "/upload-session",
    # IMPORTANT: removed response_model=schemas.SessionCreateResponse to avoid the AttributeError
    dependencies=[Depends(dev_auth)],
)
def create_session(body: schemas.SessionCreate, db: Session = Depends(get_db)):
    """
    Creates a new session row and returns a generated sessionId.
    """
    # verify patient exists
    patient = db.query(models.Patient).filter(models.Patient.id == body.patientId).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    session_id = f"session_{uuid.uuid4().hex}"

    s = models.Session(
        id=session_id,
        patient_id=body.patientId,
        user_id=body.userId,
        patient_name=body.patientName,
        status=body.status,
        start_time=body.startTime,
        template_id=body.templateId,
    )
    db.add(s)
    db.commit()

    # return plain dict, no schema needed
    return {"sessionId": session_id}


@router.post(
    "/get-presigned-url",
    response_model=schemas.PresignResponse,
    dependencies=[Depends(dev_auth)],
)
def get_presigned_url(body: schemas.PresignRequest, request: Request):
    """
    Returns:
    - url: backend PUT endpoint for uploading the chunk (/v1/mock-upload/...)
    - gcsPath: the "path" in storage for this chunk
    - publicUrl: public URL to access the final stored object
    """
    # Supabase object path inside bucket
    object_key = f"sessions/{body.sessionId}/chunk_{body.chunkNumber}.wav"

    # backend upload URL: client will PUT the file here
    upload_url = str(
        request.url_for("mock_upload_chunk", session_id=body.sessionId, chunk_number=body.chunkNumber)
    )

    gcs_path = object_key
    public_url = get_public_url(object_key)

    return schemas.PresignResponse(
        url=upload_url,
        gcsPath=gcs_path,
        publicUrl=public_url,
    )


@router.put(
    "/mock-upload/{session_id}/{chunk_number}",
    name="mock_upload_chunk",
)
async def mock_upload_chunk(
    session_id: str,
    chunk_number: int,
    file: UploadFile = File(...),
    _auth=Depends(dev_auth),
) -> Any:
    """
    Receives the audio chunk from the client and stores it locally.
    Later, /v1/notify-chunk-uploaded will push it to Supabase.
    """
    session_dir = os.path.join(FILE_STORAGE_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)
    dest_path = os.path.join(session_dir, f"chunk_{chunk_number}.wav")

    with open(dest_path, "wb") as f:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)

    return {
        "status": "uploaded",
        "sessionId": session_id,
        "chunkNumber": chunk_number,
    }


@router.post(
    "/notify-chunk-uploaded",
    response_model=schemas.NotifyChunkResponse,
    dependencies=[Depends(dev_auth)],
)
def notify_chunk_uploaded(body: schemas.NotifyChunkRequest, db: Session = Depends(get_db)):
    """
    After the client has uploaded the chunk to /mock-upload, they call this.
    Here we:
    - Upload the local file to Supabase Storage.
    - Save chunk metadata in DB.
    """
    local_path = os.path.join(
        FILE_STORAGE_DIR,
        body.sessionId,
        f"chunk_{body.chunkNumber}.wav",
    )

    if not os.path.exists(local_path):
        logger.error("Local chunk file not found at %s", local_path)
        raise HTTPException(status_code=400, detail="Local chunk file not found; upload may have failed")

    # Upload to Supabase Storage using gcsPath as object key
    try:
        supabase_public_url = upload_file_from_path(local_path, body.gcsPath)
    except Exception as e:
        logger.exception("Failed to upload chunk to Supabase")
        raise HTTPException(status_code=500, detail=f"Supabase upload failed: {e}")

    # Persist metadata in DB
    chunk = models.AudioChunk(
        session_id=body.sessionId,
        chunk_number=body.chunkNumber,
        gcs_path=body.gcsPath,
        public_url=supabase_public_url,
        mime_type=body.mimeType,
        is_last=body.isLast,
        total_chunks_client=body.totalChunksClient,
    )
    db.add(chunk)
    db.commit()

    return schemas.NotifyChunkResponse(success=True)
