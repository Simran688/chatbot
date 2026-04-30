"""
Chat history model for storing user queries and AI responses.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class ChatHistory(Base):
    """
    Chat history model storing all user queries and AI responses.
    """
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Query and response
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    
    # Source tracking
    source_documents = Column(Text, nullable=True)  # JSON array of document names used
    sources = Column(Text, nullable=True)  # JSON array of source snippets
    
    # Query routing info
    query_type = Column(String(50), nullable=True)  # "internal" or "general"
    used_web_search = Column(Integer, default=0, nullable=False)  # 0=no, 1=yes
    
    # Performance metrics
    response_time_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    
    # Feedback (optional)
    user_rating = Column(Integer, nullable=True)  # 1-5 rating
    user_feedback = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chat_history")

    def __repr__(self) -> str:
        return f"<ChatHistory(id={self.id}, user_id={self.user_id}, query={self.query[:50]}...)>"
