from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

# Document type enum
class DocumentType(str, Enum):
    PDF = "pdf"
    TXT = "txt"
    CSV = "csv"
    JSON = "json"
    DOCX = "docx"
    OTHER = "other"

# Document metadata schema
class DocumentMetadata(BaseModel):
    page_count: Optional[int] = None
    author: Optional[str] = None
    creation_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    custom_metadata: Optional[Dict[str, Any]] = None

# Document output schema
class DocumentOut(BaseModel):
    id: str = Field(..., alias="_id")
    filename: str
    original_filename: str
    uploader_id: str
    upload_date: datetime
    file_size: int
    file_type: str
    is_embedded: bool
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        allow_population_by_field_name = True

# Document list response
class DocumentList(BaseModel):
    total: int
    documents: List[DocumentOut]

# Document update schema
class DocumentUpdate(BaseModel):
    metadata: Optional[DocumentMetadata] = None
    is_embedded: Optional[bool] = None

# Document embedding status response
class DocumentEmbeddingStatus(BaseModel):
    document_id: str
    is_embedded: bool
    status: str
    message: Optional[str] = None
