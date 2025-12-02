# app/schemas.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

# Patients

class PatientCreate(BaseModel):
    name: str
    userId: str

class PatientOut(BaseModel):
    id: int
    name: str
    userId: str

    model_config = ConfigDict(from_attributes=True)

# Templates

class TemplateOut(BaseModel):
    templateId: str
    name: str
    model_config = ConfigDict(from_attributes=True)

# Recording / Sessions

class SessionCreate(BaseModel):
    patientId: int
    userId: str
    patientName: str
    status: str
    startTime: datetime
    templateId: Optional[str] = None

class SessionOut(BaseModel):
    id: str
    patientId: int
    userId: str
    patientName: str
    status: str
    startTime: Optional[datetime] = None
    templateId: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
class PresignRequest(BaseModel):
    sessionId: str
    chunkNumber: int
    mimeType: str = "audio/wav"

class PresignResponse(BaseModel):
    url: str
    gcsPath: str
    publicUrl: str

class NotifyChunkRequest(BaseModel):
    sessionId: str
    gcsPath: str
    chunkNumber: int
    isLast: bool = False
    totalChunksClient: int = 0
    mimeType: str = "audio/wav"
    selectedTemplate: Optional[str] = None
    selectedTemplateId: Optional[str] = None
    model: Optional[str] = None  # "fast" / "accurate" from docs

class NotifyChunkResponse(BaseModel):
    success: bool
