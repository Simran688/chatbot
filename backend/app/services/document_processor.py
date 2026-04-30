"""
Document text extraction and chunking service.
"""

import io
import os
from pathlib import Path
from typing import List, Optional

from PyPDF2 import PdfReader
from docx import Document as DocxDocument
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.core.config import settings


def extract_text_from_pdf(file_content: bytes) -> str:
    """
    Extract text from PDF file content.
    
    Args:
        file_content: Raw bytes of PDF file
        
    Returns:
        Extracted text as string
    """
    text = ""
    try:
        pdf_file = io.BytesIO(file_content)
        reader = PdfReader(pdf_file)
        
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
                
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    return text.strip()


def extract_text_from_docx(file_content: bytes) -> str:
    """
    Extract text from DOCX file content.
    
    Args:
        file_content: Raw bytes of DOCX file
        
    Returns:
        Extracted text as string
    """
    text = ""
    try:
        doc_file = io.BytesIO(file_content)
        doc = DocxDocument(doc_file)
        
        for para in doc.paragraphs:
            if para.text.strip():
                text += para.text + "\n"
                
    except Exception as e:
        raise ValueError(f"Failed to extract text from DOCX: {str(e)}")
    
    return text.strip()


def extract_text(file_content: bytes, file_extension: str) -> str:
    """
    Extract text from file based on extension.
    
    Args:
        file_content: Raw file bytes
        file_extension: File extension (pdf, docx, etc.)
        
    Returns:
        Extracted text
        
    Raises:
        ValueError: If file type not supported
    """
    ext = file_extension.lower().lstrip('.')
    
    if ext == 'pdf':
        return extract_text_from_pdf(file_content)
    elif ext in ['docx', 'doc']:
        return extract_text_from_docx(file_content)
    elif ext == 'txt':
        return file_content.decode('utf-8')
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    separators: Optional[List[str]] = None
) -> List[str]:
    """
    Split text into overlapping chunks for embedding.
    
    Args:
        text: Input text to chunk
        chunk_size: Size of each chunk in characters
        chunk_overlap: Overlap between chunks
        separators: List of separators to use for splitting
        
    Returns:
        List of text chunks
    """
    if not separators:
        separators = ["\n\n", "\n", ". ", " ", ""]
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
        length_function=len,
    )
    
    chunks = text_splitter.split_text(text)
    return chunks


def save_upload_file(file_content: bytes, filename: str, upload_dir: str = "./uploads") -> str:
    """
    Save uploaded file to disk.
    
    Args:
        file_content: Raw file bytes
        filename: Original filename
        upload_dir: Directory to save files
        
    Returns:
        Path to saved file
    """
    # Create upload directory if not exists
    Path(upload_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    import uuid
    unique_name = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(upload_dir, unique_name)
    
    # Save file
    with open(file_path, 'wb') as f:
        f.write(file_content)
    
    return file_path
