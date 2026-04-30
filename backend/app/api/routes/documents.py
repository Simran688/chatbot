"""
Document upload and management API endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document, DocumentSource
from app.schemas.document import (
    DocumentResponse,
    DocumentUploadResponse,
    DocumentListResponse,
    VectorStoreStats,
)
from app.services.document_processor import (
    extract_text,
    chunk_text,
    save_upload_file,
)
from app.services.embedding_service import embedding_service
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    description: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a document (PDF, DOCX) and process it for RAG.
    
    Steps:
    1. Save file to disk
    2. Extract text
    3. Chunk text
    4. Generate embeddings
    5. Store in FAISS
    6. Save metadata to DB
    """
    # Validate file type
    allowed_types = ['.pdf', '.docx', '.doc', '.txt']
    file_ext = '.' + file.filename.split('.')[-1].lower()
    
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_types)}"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Save file to disk
        file_path = save_upload_file(file_content, file.filename)
        
        # Create database record
        db_document = Document(
            name=file.filename,
            original_filename=file.filename,
            file_path=file_path,
            source=DocumentSource.UPLOAD,
            file_type=file_ext.lstrip('.'),
            uploaded_by=current_user.id,
            file_size=file_size,
            description=description,
            is_processed=0,  # Mark as processing
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        # Extract text
        text = extract_text(file_content, file_ext)
        
        if not text:
            db_document.is_processed = 2  # Error
            db_document.processing_error = "No text extracted from document"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract text from document"
            )
        
        # Chunk text
        chunks = chunk_text(text, chunk_size=1000, chunk_overlap=200)
        
        if not chunks:
            db_document.is_processed = 2
            db_document.processing_error = "Text too short to chunk"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Document text is too short"
            )
        
        # Generate embeddings and add to FAISS
        metadatas = [
            {
                "chunk_index": i,
                "total_chunks": len(chunks),
                "filename": file.filename,
            }
            for i in range(len(chunks))
        ]
        
        embedding_service.add_documents(
            texts=chunks,
            metadatas=metadatas,
            document_id=db_document.id
        )
        
        # Mark as processed
        db_document.is_processed = 1
        db.commit()
        db.refresh(db_document)
        
        return DocumentUploadResponse(
            message="Document uploaded and processed successfully",
            document=DocumentResponse.model_validate(db_document),
            chunks_created=len(chunks)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Update error status if document exists
        if 'db_document' in locals() and db_document.id:
            db_document.is_processed = 2
            db_document.processing_error = str(e)
            db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )


@router.get("/", response_model=DocumentListResponse)
def list_documents(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all uploaded documents.
    """
    total = db.query(Document).count()
    documents = db.query(Document).offset(skip).limit(limit).all()
    
    return DocumentListResponse(
        total=total,
        documents=[DocumentResponse.model_validate(doc) for doc in documents]
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific document by ID.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentResponse.model_validate(document)


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a document and its embeddings.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete from FAISS
    embedding_service.delete_document(document_id)
    
    # Delete from DB
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}


@router.get("/stats/vectors", response_model=VectorStoreStats)
def get_vector_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get vector store statistics.
    """
    stats = embedding_service.get_stats()
    return VectorStoreStats(**stats)
