"""
Document model for storing uploaded file metadata.
"""

from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base import Base


class DocumentSource(str, enum.Enum):
    """Source of the document."""
    UPLOAD = "upload"
    GOOGLE_DRIVE = "google_drive"


class AccessLevel(str, enum.Enum):
    """Access level for documents."""
    PUBLIC = "public"
    PRIVATE = "private"
    RESTRICTED = "restricted"


class Document(Base):
    """
    Document model storing metadata about uploaded files.
    Actual content is stored in FAISS vector database.
    """
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=True)  # Local path if stored
    source = Column(Enum(DocumentSource), default=DocumentSource.UPLOAD, nullable=False)
    access_level = Column(Enum(AccessLevel), default=AccessLevel.PUBLIC, nullable=False)
    file_type = Column(String(50), nullable=True)  # pdf, docx, etc.
    file_size = Column(Integer, nullable=True)  # in bytes
    
    # For Google Drive integration
    google_drive_file_id = Column(String(255), nullable=True, unique=True)
    
    # Foreign key to uploader
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Optional: store a summary or description
    description = Column(Text, nullable=True)
    
    # Status tracking
    is_processed = Column(Integer, default=0, nullable=False)  # 0=pending, 1=processed, 2=error
    processing_error = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    uploaded_by_user = relationship("User", back_populates="uploaded_documents")

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, name={self.name}, source={self.source})>"
