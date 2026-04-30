"""
Google Drive integration service.
Fetches files from Google Drive and processes them for RAG.
"""

import os
import io
from typing import List, Dict, Optional
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

from app.core.config import settings
from app.services.document_processor import extract_text, chunk_text
from app.services.embedding_service import embedding_service


# Google Drive API scopes
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


class GoogleDriveService:
    """
    Service for fetching and processing Google Drive files.
    """
    
    # Supported file types for text extraction
    SUPPORTED_MIME_TYPES = {
        'application/pdf': '.pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
        'application/vnd.google-apps.document': 'gdoc',  # Google Docs (export as)
        'text/plain': '.txt',
    }
    
    def __init__(self):
        self.credentials_path = settings.GOOGLE_DRIVE_CREDENTIALS_PATH
        self.token_path = os.path.join(
            os.path.dirname(self.credentials_path), 
            'token.json'
        )
        self.service = None
    
    def _get_credentials(self) -> Optional[Credentials]:
        """
        Get or refresh Google Drive credentials.
        
        Returns:
            Credentials object or None if not available
        """
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        
        # If no valid credentials, need to authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Google credentials file not found: {self.credentials_path}. "
                        "Please download credentials.json from Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save token for future runs
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        return creds
    
    def connect(self) -> bool:
        """
        Connect to Google Drive API.
        
        Returns:
            True if connection successful
        """
        try:
            creds = self._get_credentials()
            self.service = build('drive', 'v3', credentials=creds, cache_discovery=False)
            return True
        except Exception as e:
            print(f"Failed to connect to Google Drive: {e}")
            return False
    
    def list_files(
        self,
        folder_id: Optional[str] = None,
        query: Optional[str] = None,
        max_results: int = 100
    ) -> List[Dict]:
        """
        List files in Google Drive.
        
        Args:
            folder_id: Specific folder to list (None for root)
            query: Additional search query
            max_results: Maximum files to return
            
        Returns:
            List of file metadata
        """
        if not self.service:
            if not self.connect():
                return []
        
        try:
            # Build query
            q = "trashed = false"
            
            if folder_id:
                q += f" and '{folder_id}' in parents"
            else:
                q += " and 'root' in parents"
            
            # Filter by supported mime types
            mime_types = " or ".join([
                f"mimeType='{mime}'" 
                for mime in self.SUPPORTED_MIME_TYPES.keys()
            ])
            q += f" and ({mime_types})"
            
            if query:
                q += f" and name contains '{query}'"
            
            results = (
                self.service.files()
                .list(
                    q=q,
                    pageSize=max_results,
                    fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, webViewLink)"
                )
                .execute()
            )
            
            return results.get('files', [])
            
        except HttpError as e:
            print(f"Google Drive API error: {e}")
            return []
    
    def download_file(self, file_id: str, mime_type: str) -> Optional[bytes]:
        """
        Download file from Google Drive.
        
        Args:
            file_id: Google Drive file ID
            mime_type: File MIME type
            
        Returns:
            File content as bytes or None
        """
        if not self.service:
            return None
        
        try:
            # Handle Google Docs export
            if mime_type == 'application/vnd.google-apps.document':
                request = self.service.files().export_media(
                    fileId=file_id,
                    mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )
            else:
                request = self.service.files().get_media(fileId=file_id)
            
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print(f"Download {int(status.progress() * 100)}%")
            
            return fh.getvalue()
            
        except HttpError as e:
            print(f"Failed to download file {file_id}: {e}")
            return None
    
    def get_file_extension(self, mime_type: str) -> str:
        """
        Get file extension from MIME type.
        
        Args:
            mime_type: MIME type
            
        Returns:
            File extension
        """
        return self.SUPPORTED_MIME_TYPES.get(mime_type, '.unknown')
    
    def process_file(
        self,
        file_id: str,
        file_name: str,
        mime_type: str,
        document_db_id: int
    ) -> Dict:
        """
        Download and process a Google Drive file.
        
        Args:
            file_id: Google Drive file ID
            file_name: File name
            mime_type: File MIME type
            document_db_id: Database document ID
            
        Returns:
            Processing result with chunk count
        """
        # Download file
        file_content = self.download_file(file_id, mime_type)
        
        if not file_content:
            return {
                "success": False,
                "error": "Failed to download file",
                "chunks": 0
            }
        
        try:
            # Get file extension
            file_ext = self.get_file_extension(mime_type)
            if file_ext == '.unknown':
                return {
                    "success": False,
                    "error": f"Unsupported file type: {mime_type}",
                    "chunks": 0
                }
            
            # Extract text
            text = extract_text(file_content, file_ext)
            
            if not text:
                return {
                    "success": False,
                    "error": "No text extracted from document",
                    "chunks": 0
                }
            
            # Chunk text
            chunks = chunk_text(text, chunk_size=1000, chunk_overlap=200)
            
            if not chunks:
                return {
                    "success": False,
                    "error": "Text too short to chunk",
                    "chunks": 0
                }
            
            # Generate embeddings and add to FAISS
            metadatas = [
                {
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "filename": file_name,
                    "source": "google_drive",
                    "google_drive_file_id": file_id,
                }
                for i in range(len(chunks))
            ]
            
            embedding_service.add_documents(
                texts=chunks,
                metadatas=metadatas,
                document_id=document_db_id
            )
            
            return {
                "success": True,
                "error": None,
                "chunks": len(chunks)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "chunks": 0
            }


# Global Google Drive service instance
google_drive_service = GoogleDriveService()
