from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    RESUME = "resume"
    JOB_DESCRIPTION = "job_description"

class FileFormat(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"

class DocumentUpload(BaseModel):
    filename: str
    content_type: str
    size: int

class ParsedDocument(BaseModel):
    id: Optional[str] = None
    filename: str
    document_type: DocumentType
    file_format: FileFormat
    raw_content: str
    structured_content: Dict[str, Any]
    parsed_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

class DocumentResponse(BaseModel):
    id: str
    filename: str
    document_type: DocumentType
    status: str
    message: str
    parsed_at: datetime
