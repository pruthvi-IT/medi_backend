from pydantic import BaseModel
from typing import Optional, List

class CreateSessionReq(BaseModel):
    patientId: str
    userId: str
    patientName: str
    status: Optional[str] = "recording"
    startTime: Optional[str] = None
    templateId: Optional[str] = None

class CreateSessionResp(BaseModel):
    id: str

class PresignedReq(BaseModel):
    sessionId: str
    chunkNumber: int
    mimeType: str

class PresignedResp(BaseModel):
    url: str
    gcsPath: str
    publicUrl: Optional[str] = None

class NotifyChunkReq(BaseModel):
    sessionId: str
    gcsPath: str
    chunkNumber: int
    isLast: bool = False
    totalChunksClient: Optional[int] = 0
    publicUrl: Optional[str] = None
    mimeType: Optional[str] = None
    selectedTemplate: Optional[str] = None
    selectedTemplateId: Optional[str] = None
    model: Optional[str] = None

class PatientCreateReq(BaseModel):
    name: str
    userId: str

class PatientResp(BaseModel):
    id: str
    name: str
