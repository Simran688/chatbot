"""
Pydantic schemas for query and chat APIs.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


# Query request
class QueryRequest(BaseModel):
    """Request to query the RAG system."""
    query: str
    top_k: int = 5
    include_sources: bool = True
    query_type: Optional[str] = None  # "internal", "general", or None for auto


# Source snippet
class SourceSnippet(BaseModel):
    """Relevant text chunk from a document."""
    text: str
    document: str
    chunk_index: int
    relevance_score: float


# Web search result
class WebSearchResult(BaseModel):
    """Web search result."""
    title: str
    url: str
    snippet: str


# Query response
class QueryResponse(BaseModel):
    """Response from RAG query."""
    query: str
    answer: str
    source_documents: List[str]
    source_snippets: List[SourceSnippet]
    query_type: str  # "internal" or "general"
    used_web_search: bool
    response_time_ms: Optional[int] = None
    web_results: Optional[List[WebSearchResult]] = None


# Chat history item
class ChatHistoryItem(BaseModel):
    """Single chat interaction."""
    id: int
    query: str
    response: str
    source_documents: Optional[str]  # JSON string
    query_type: Optional[str]
    used_web_search: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Chat history list
class ChatHistoryList(BaseModel):
    """List of chat history."""
    total: int
    history: List[ChatHistoryItem]


# Combined response (internal + web)
class CombinedQueryResponse(QueryResponse):
    """Response that may include web search results."""
    web_results: Optional[List[WebSearchResult]] = None
    confidence_score: Optional[float] = None
