"""
Google Drive integration API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document, DocumentSource
from app.schemas.document import DocumentResponse, DocumentUploadResponse
from app.services.google_drive import google_drive_service
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter(prefix="/google-drive", tags=["Google Drive"])


@router.get("/status")
def get_connection_status(
    current_user: User = Depends(get_current_user)
):
    """
    Check Google Drive connection status.
    """
    is_connected = google_drive_service.connect()
    
    if is_connected:
        return {
            "status": "connected",
            "message": "Google Drive API connection successful"
        }
    else:
        return {
            "status": "disconnected",
            "message": "Failed to connect to Google Drive. Check credentials."
        }


@router.get("/files")
def list_drive_files(
    folder_id: Optional[str] = None,
    query: Optional[str] = None,
    max_results: int = 100,
    current_user: User = Depends(get_current_user)
):
    """
    List available files in Google Drive.
    
    Returns files that can be processed (PDF, DOCX, Google Docs, TXT).
    """
    if not google_drive_service.connect():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to connect to Google Drive. Check credentials."
        )
    
    files = google_drive_service.list_files(
        folder_id=folder_id,
        query=query,
        max_results=max_results
    )
    
    return {
        "total": len(files),
        "files": [
            {
                "id": f["id"],
                "name": f["name"],
                "mime_type": f["mimeType"],
                "size": f.get("size"),
                "modified_time": f.get("modifiedTime"),
                "web_view_link": f.get("webViewLink")
            }
            for f in files
        ]
    }


@router.post("/sync/{file_id}", response_model=DocumentUploadResponse)
def sync_file(
    file_id: str,
    background_tasks: BackgroundTasks,
    description: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sync a single file from Google Drive.
    
    Downloads the file, extracts text, chunks it, and adds to vector store.
    """
    # Check connection
    if not google_drive_service.connect():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to connect to Google Drive"
        )
    
    try:
        # Get file metadata from Google Drive
        from googleapiclient.errors import HttpError
        
        try:
            file_metadata = (
                google_drive_service.service.files()
                .get(fileId=file_id, fields="id, name, mimeType, size")
                .execute()
            )
        except HttpError as e:
            if e.resp.status == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found in Google Drive"
                )
            raise
        
        file_name = file_metadata["name"]
        mime_type = file_metadata["mimeType"]
        file_size = int(file_metadata.get("size", 0))
        
        # Check if file already synced
        existing = (
            db.query(Document)
            .filter(Document.google_drive_file_id == file_id)
            .first()
        )
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"File already synced (Document ID: {existing.id})"
            )
        
        # Create database record
        db_document = Document(
            name=file_name,
            original_filename=file_name,
            source=DocumentSource.GOOGLE_DRIVE,
            file_type=google_drive_service.get_file_extension(mime_type),
            file_size=file_size,
            google_drive_file_id=file_id,
            description=description,
            is_processed=0,
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        # Process file
        result = google_drive_service.process_file(
            file_id=file_id,
            file_name=file_name,
            mime_type=mime_type,
            document_db_id=db_document.id
        )
        
        if not result["success"]:
            db_document.is_processed = 2  # Error
            db_document.processing_error = result["error"]
            db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to process file: {result['error']}"
            )
        
        # Mark as processed
        db_document.is_processed = 1
        db.commit()
        db.refresh(db_document)
        
        return DocumentUploadResponse(
            message="Google Drive file synced successfully",
            document=DocumentResponse.model_validate(db_document),
            chunks_created=result["chunks"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync file: {str(e)}"
        )


@router.post("/sync-all")
def sync_all_files(
    folder_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sync all supported files from a Google Drive folder.
    
    Args:
        folder_id: Folder to sync (None for root)
    """
    if not google_drive_service.connect():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to connect to Google Drive"
        )
    
    # List files
    files = google_drive_service.list_files(folder_id=folder_id, max_results=100)
    
    if not files:
        return {
            "message": "No files found to sync",
            "synced": 0,
            "failed": 0,
            "results": []
        }
    
    results = []
    synced_count = 0
    failed_count = 0
    
    for file_info in files:
        file_id = file_info["id"]
        file_name = file_info["name"]
        mime_type = file_info["mimeType"]
        
        try:
            # Check if already synced
            existing = (
                db.query(Document)
                .filter(Document.google_drive_file_id == file_id)
                .first()
            )
            
            if existing:
                results.append({
                    "file_id": file_id,
                    "name": file_name,
                    "status": "skipped",
                    "reason": "Already synced",
                    "document_id": existing.id
                })
                continue
            
            # Create DB record
            db_document = Document(
                name=file_name,
                original_filename=file_name,
                source=DocumentSource.GOOGLE_DRIVE,
                file_type=google_drive_service.get_file_extension(mime_type),
                google_drive_file_id=file_id,
                is_processed=0,
            )
            db.add(db_document)
            db.commit()
            db.refresh(db_document)
            
            # Process file
            process_result = google_drive_service.process_file(
                file_id=file_id,
                file_name=file_name,
                mime_type=mime_type,
                document_db_id=db_document.id
            )
            
            if process_result["success"]:
                db_document.is_processed = 1
                db.commit()
                synced_count += 1
                results.append({
                    "file_id": file_id,
                    "name": file_name,
                    "status": "synced",
                    "document_id": db_document.id,
                    "chunks": process_result["chunks"]
                })
            else:
                db_document.is_processed = 2
                db_document.processing_error = process_result["error"]
                db.commit()
                failed_count += 1
                results.append({
                    "file_id": file_id,
                    "name": file_name,
                    "status": "failed",
                    "error": process_result["error"]
                })
                
        except Exception as e:
            failed_count += 1
            results.append({
                "file_id": file_id,
                "name": file_name,
                "status": "failed",
                "error": str(e)
            })
    
    return {
        "message": f"Sync complete: {synced_count} synced, {failed_count} failed",
        "synced": synced_count,
        "failed": failed_count,
        "results": results
    }
