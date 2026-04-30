"""
Query API endpoints for RAG chat.
"""

import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.chat_history import ChatHistory
from app.schemas.query import (
    QueryRequest,
    QueryResponse,
    SourceSnippet,
    WebSearchResult,
    ChatHistoryList,
)
from app.services.rag_pipeline import rag_pipeline
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter(prefix="/query", tags=["Query"])


@router.post("/", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Query the RAG system to get answers from uploaded documents.
    
    Steps:
    1. Classify query type (internal/general)
    2. If internal: retrieve from FAISS + generate response
    3. If general: use web search (Step 6)
    4. Save to chat history
    """
    start_time = time.time()
    
    try:
        # Run RAG pipeline (now async)
        rag_response = await rag_pipeline.run(
            query=request.query,
            top_k=request.top_k,
            force_query_type=request.query_type if hasattr(request, 'query_type') else None
        )
        
        # Calculate response time
        response_time = int((time.time() - start_time) * 1000)
        
        # Map to response model
        source_snippets = [
            SourceSnippet(**snippet)
            for snippet in rag_response.source_snippets
        ]
        
        # Convert web results if present
        web_results = None
        if rag_response.web_results:
            web_results = [
                WebSearchResult(**result)
                for result in rag_response.web_results
            ]
        
        response = QueryResponse(
            query=request.query,
            answer=rag_response.answer,
            source_documents=rag_response.source_documents,
            source_snippets=source_snippets if request.include_sources else [],
            query_type=rag_response.query_type,
            used_web_search=rag_response.used_web_search,
            response_time_ms=response_time,
            web_results=web_results
        )
        
        # Save to chat history
        chat_entry = ChatHistory(
            user_id=current_user.id,
            query=request.query,
            response=rag_response.answer,
            source_documents=str(rag_response.source_documents),
            sources=str(rag_response.source_snippets) if request.include_sources else None,
            query_type=rag_response.query_type,
            used_web_search=1 if rag_response.used_web_search else 0,
            response_time_ms=response_time,
        )
        db.add(chat_entry)
        db.commit()
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )


@router.get("/history", response_model=ChatHistoryList)
def get_chat_history(
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get chat history for a user.
    """
    total = db.query(ChatHistory).filter(ChatHistory.user_id == current_user.id).count()
    
    history = (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == current_user.id)
        .order_by(ChatHistory.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return ChatHistoryList(
        total=total,
        history=history
    )


@router.delete("/history/{chat_id}")
def delete_chat_entry(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a specific chat history entry.
    """
    chat = (
        db.query(ChatHistory)
        .filter(ChatHistory.id == chat_id, ChatHistory.user_id == current_user.id)
        .first()
    )
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat entry not found"
        )
    
    db.delete(chat)
    db.commit()
    
    return {"message": "Chat entry deleted successfully"}
