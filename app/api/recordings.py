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
    - url: backend PUT endpoint for uploading the chunk (/v1/upload-chunk/...)
    - storagePath: the path in Supabase Storage for this chunk
    """
    # Supabase object path inside bucket
    storage_path = f"sessions/{body.sessionId}/chunk_{body.chunkNumber}.m4a"

    # backend upload URL: client will PUT the file here
    upload_url = str(
        request.url_for("upload_chunk", session_id=body.sessionId, chunk_number=body.chunkNumber)
    )

    return schemas.PresignResponse(
        url=upload_url,
        storagePath=storage_path,
    )


@router.put(
    "/upload-chunk/{session_id}/{chunk_number}",
    name="upload_chunk",
    dependencies=[Depends(dev_auth)],
)
async def upload_chunk(
    session_id: str,
    chunk_number: int,
    file: UploadFile = File(...),
) -> Any:
    """
    Receives the audio chunk from the client and uploads it directly to Supabase Storage.
    """
    from app.supabase_storage import get_client, SUPABASE_BUCKET, ensure_bucket_exists

    storage_path = f"sessions/{session_id}/chunk_{chunk_number}.m4a"

    try:
        # Read file content
        content = await file.read()

        # Get Supabase client
        client = get_client()

        # Try to upload to Supabase Storage
        try:
            client.storage.from_(SUPABASE_BUCKET).upload(
                storage_path,
                content,
                file_options={"content-type": file.content_type or "audio/m4a"},
            )
        except Exception as e:
            # If bucket doesn't exist, create it and retry
            if "Bucket not found" in str(e):
                logger.warning("Bucket '%s' not found, creating...", SUPABASE_BUCKET)
                ensure_bucket_exists()
                client.storage.from_(SUPABASE_BUCKET).upload(
                    storage_path,
                    content,
                    file_options={"content-type": file.content_type or "audio/m4a"},
                )
            else:
                raise

        logger.info("Uploaded chunk to Supabase: %s", storage_path)

        return {
            "status": "uploaded",
            "sessionId": session_id,
            "chunkNumber": chunk_number,
            "storagePath": storage_path,
        }

    except Exception as e:
        logger.error("Failed to upload chunk to Supabase: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post(
    "/notify-chunk-uploaded",
    response_model=schemas.NotifyChunkResponse,
    dependencies=[Depends(dev_auth)],
)
def notify_chunk_uploaded(body: schemas.NotifyChunkRequest, db: Session = Depends(get_db)):
    """
    After the client has uploaded the chunk via /upload-chunk, they call this
    to store the chunk metadata in the database.
    """
    from app.supabase_storage import get_public_url

    # Generate public URL from storagePath
    public_url = get_public_url(body.storagePath)

    # Persist metadata in DB (using gcs_path column for storagePath)
    chunk = models.AudioChunk(
        session_id=body.sessionId,
        chunk_number=body.chunkNumber,
        gcs_path=body.storagePath,  # storing storagePath in gcs_path column
        public_url=public_url,
        mime_type=body.mimeType,
        is_last=body.isLast,
        total_chunks_client=body.totalChunksClient,
    )
    db.add(chunk)
    db.commit()

    return schemas.NotifyChunkResponse(success=True, downloadUrl=public_url)
