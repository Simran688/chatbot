"""
Pydantic schemas for document-related API requests/responses.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from app.models.document import DocumentSource, AccessLevel


# Shared properties
class DocumentBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    access_level: AccessLevel = AccessLevel.PUBLIC


# Properties for creating a document
class DocumentCreate(DocumentBase):
    pass


# Properties returned by API
class DocumentResponse(DocumentBase):
    id: int
    original_filename: str
    source: DocumentSource
    file_type: Optional[str]
    file_size: Optional[int]
    is_processed: int
    processing_error: Optional[str]
    uploaded_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Document upload response
class DocumentUploadResponse(BaseModel):
    message: str
    document: DocumentResponse
    chunks_created: int


# Document list response
class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentResponse]


# Document processing status
class DocumentStatusResponse(BaseModel):
    id: int
    name: str
    is_processed: int
    processing_error: Optional[str]
    chunk_count: Optional[int]


# Vector store stats
class VectorStoreStats(BaseModel):
    total_vectors: int
    total_documents: int
    dimension: int
