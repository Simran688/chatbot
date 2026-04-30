"""
RAG (Retrieval-Augmented Generation) Pipeline.
Builds the LangChain pipeline for answering queries using retrieved context.
"""

import asyncio
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough, RunnableLambda

from app.core.config import settings
from app.services.embedding_service import embedding_service
from app.services.web_search import web_search_service


@dataclass
class RAGResponse:
    """Structured response from RAG pipeline."""
    answer: str
    source_documents: List[str]  # Document names used
    source_snippets: List[Dict]  # Relevant chunks with metadata
    query_type: str  # "internal" or "general"
    used_web_search: bool = False
    web_results: List[Dict] = field(default_factory=list)  # Web search results


# RAG Prompt Template
RAG_PROMPT_TEMPLATE = """You are an Enterprise Policy & Knowledge Assistant. Answer the user's question based ONLY on the provided context documents.

If the context doesn't contain enough information to answer the question, say "I don't have enough information to answer this question based on the available documents."

Do not make up information or use outside knowledge. Be concise and accurate.

---

CONTEXT:
{context}

---

QUESTION: {question}

---

Provide a clear, accurate answer based on the context above. If multiple sources provide different information, synthesize them."""

# Web search prompt template
WEB_SEARCH_PROMPT_TEMPLATE = """You are a helpful AI assistant. Answer the user's question using the web search results provided below.

Be concise, accurate, and helpful. Synthesize information from multiple sources if available. Cite the sources in your answer when possible.

---

WEB SEARCH RESULTS:
{context}

---

QUESTION: {question}

---

Provide a clear, accurate answer based on the web search results above."""

# Query classification prompt
QUERY_CLASSIFICATION_PROMPT = """Analyze this query and determine if it's asking about internal company policies/documents or general knowledge.

Query: {query}

Respond with ONLY one word:
- "internal" if asking about company policies, procedures, HR rules, internal documents, employee handbook, benefits, etc.
- "general" if asking about general knowledge, facts, news, definitions, etc.

Response:"""


class RAGPipeline:
    """
    RAG pipeline using LangChain for retrieval and response generation.
    """
    
    def __init__(self):
        # Initialize LLM
        self.llm = ChatOpenAI(
            model_name=settings.OPENAI_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.1,  # Low temperature for factual responses
        )
        
        # RAG prompt for internal docs
        self.rag_prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
        
        # Web search prompt for general queries
        self.web_prompt = ChatPromptTemplate.from_template(WEB_SEARCH_PROMPT_TEMPLATE)
        
        # Query classifier
        self.classifier_prompt = ChatPromptTemplate.from_template(QUERY_CLASSIFICATION_PROMPT)
    
    def format_context(self, chunks: List[Tuple[str, Dict, float]]) -> str:
        """
        Format retrieved chunks into context string.
        
        Args:
            chunks: List of (text, metadata, distance) tuples
            
        Returns:
            Formatted context string
        """
        context_parts = []
        for i, (text, metadata, distance) in enumerate(chunks, 1):
            source = metadata.get('filename', 'Unknown')
            chunk_idx = metadata.get('chunk_index', 0)
            
            context_parts.append(
                f"[Document {i}: {source} - Chunk {chunk_idx}]\n{text}\n"
            )
        
        return "\n".join(context_parts)
    
    def classify_query(self, query: str) -> str:
        """
        Classify if query is internal or general.
        
        Args:
            query: User question
            
        Returns:
            "internal" or "general"
        """
        chain = self.classifier_prompt | self.llm | StrOutputParser()
        result = chain.invoke({"query": query}).strip().lower()
        
        return "internal" if "internal" in result else "general"
    
    async def search_web(self, query: str) -> List[Dict[str, str]]:
        """
        Search the web for general knowledge queries.
        
        Args:
            query: Search query
            
        Returns:
            List of web search results
        """
        results = await web_search_service.search(query)
        return results
    
    def format_web_context(self, web_results: List[Dict[str, str]]) -> str:
        """
        Format web search results into context string.
        
        Args:
            web_results: List of web search results
            
        Returns:
            Formatted context string
        """
        if not web_results:
            return "No web search results available."
        
        context_parts = []
        for i, result in enumerate(web_results, 1):
            context_parts.append(
                f"[Source {i}: {result.get('title', 'Unknown')}]\n"
                f"URL: {result.get('url', 'N/A')}\n"
                f"Content: {result.get('snippet', 'No snippet available')}\n"
            )
        
        return "\n".join(context_parts)
    
    async def generate_web_response(
        self,
        query: str,
        web_results: List[Dict[str, str]]
    ) -> RAGResponse:
        """
        Generate response using web search results.
        
        Args:
            query: User question
            web_results: Web search results
            
        Returns:
            RAGResponse with answer
        """
        if not web_results:
            return RAGResponse(
                answer="I couldn't find relevant information from web search. Please try a different query.",
                source_documents=["web_search"],
                source_snippets=[],
                query_type="general",
                used_web_search=True,
                web_results=[]
            )
        
        # Format context
        context = self.format_web_context(web_results)
        
        # Build web search chain
        web_chain = (
            {
                "context": lambda x: context,
                "question": RunnablePassthrough()
            }
            | self.web_prompt
            | self.llm
            | StrOutputParser()
        )
        
        # Generate answer
        answer = web_chain.invoke(query)
        
        # Format source snippets
        source_snippets = [
            {
                "text": result.get('snippet', '')[:300],
                "document": result.get('title', 'Unknown'),
                "url": result.get('url', ''),
                "chunk_index": i,
                "relevance_score": 0.8  # Default score for web results
            }
            for i, result in enumerate(web_results)
        ]
        
        return RAGResponse(
            answer=answer,
            source_documents=[r.get('title', 'Unknown') for r in web_results],
            source_snippets=source_snippets,
            query_type="general",
            used_web_search=True,
            web_results=web_results
        )
    
    def retrieve_documents(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Tuple[str, Dict, float]]:
        """
        Retrieve relevant document chunks from vector store.
        
        Args:
            query: Search query
            top_k: Number of chunks to retrieve
            
        Returns:
            List of (text, metadata, distance) tuples
        """
        results = embedding_service.search(query, top_k=top_k)
        return results
    
    def generate_response(
        self,
        query: str,
        chunks: List[Tuple[str, Dict, float]]
    ) -> RAGResponse:
        """
        Generate RAG response from query and retrieved chunks.
        
        Args:
            query: User question
            chunks: Retrieved document chunks
            
        Returns:
            RAGResponse with answer and sources
        """
        if not chunks:
            return RAGResponse(
                answer="I don't have any documents to reference. Please upload relevant documents first.",
                source_documents=[],
                source_snippets=[],
                query_type="internal"
            )
        
        # Format context
        context = self.format_context(chunks)
        
        # Build RAG chain
        rag_chain = (
            {
                "context": lambda x: context,
                "question": RunnablePassthrough()
            }
            | self.rag_prompt
            | self.llm
            | StrOutputParser()
        )
        
        # Generate answer
        answer = rag_chain.invoke(query)
        
        # Extract source document names (unique)
        source_docs = list(set(
            metadata.get('filename', 'Unknown')
            for _, metadata, _ in chunks
        ))
        
        # Format source snippets
        source_snippets = [
            {
                "text": text[:300] + "..." if len(text) > 300 else text,
                "document": metadata.get('filename', 'Unknown'),
                "chunk_index": metadata.get('chunk_index', 0),
                "relevance_score": round(1 / (1 + distance), 4)  # Convert distance to similarity
            }
            for text, metadata, distance in chunks
        ]
        
        return RAGResponse(
            answer=answer,
            source_documents=source_docs,
            source_snippets=source_snippets,
            query_type="internal"
        )
    
    async def run(
        self,
        query: str,
        top_k: int = 5,
        force_query_type: Optional[str] = None
    ) -> RAGResponse:
        """
        Full RAG pipeline with query routing.
        
        Args:
            query: User question
            top_k: Number of chunks to retrieve
            force_query_type: Force "internal" or "general" (optional)
            
        Returns:
            RAGResponse
        """
        # Classify query type
        if force_query_type:
            query_type = force_query_type
        else:
            query_type = self.classify_query(query)
        
        if query_type == "internal":
            # Use internal RAG (documents)
            chunks = self.retrieve_documents(query, top_k=top_k)
            
            # If no documents found, fall back to web search
            if not chunks:
                web_results = await self.search_web(query)
                return await self.generate_web_response(query, web_results)
            
            response = self.generate_response(query, chunks)
            return response
            
        else:
            # Use web search for general queries
            web_results = await self.search_web(query)
            return await self.generate_web_response(query, web_results)


# Global RAG pipeline instance
rag_pipeline = RAGPipeline()
