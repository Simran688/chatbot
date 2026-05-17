"""
Embedding generation and FAISS vector store management.
"""

import os
import pickle
from typing import List, Dict, Optional, Tuple

import faiss
import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import settings


class EmbeddingService:
    """
    Service for generating embeddings and managing FAISS vector store.
    """
    
    def __init__(self):
        self.embedding_model = settings.HUGGINGFACE_EMBEDDING_MODEL
        self.embeddings = HuggingFaceEmbeddings(model_name=self.embedding_model)
        self.index_path = settings.FAISS_INDEX_PATH
        self.dimension = 384  # all-MiniLM-L6-v2 output size
        
        # Ensure data directory exists
        os.makedirs(self.index_path, exist_ok=True)
        
        # Initialize or load FAISS index
        self.index: Optional[faiss.Index] = None
        self.documents: List[Dict] = []  # Store metadata alongside vectors
        self._load_index()
    
    def _load_index(self) -> None:
        """Load existing FAISS index or create new one."""
        index_file = os.path.join(self.index_path, "faiss.index")
        docs_file = os.path.join(self.index_path, "documents.pkl")
        
        if os.path.exists(index_file):
            self.index = faiss.read_index(index_file)
            print(f"Loaded FAISS index with {self.index.ntotal} vectors")
        else:
            # Create new index - using IndexFlatL2 for simplicity
            self.index = faiss.IndexFlatL2(self.dimension)
            print("Created new FAISS index")
        
        # Load document metadata
        if os.path.exists(docs_file):
            with open(docs_file, 'rb') as f:
                self.documents = pickle.load(f)
    
    def _save_index(self) -> None:
        """Save FAISS index and document metadata to disk."""
        index_file = os.path.join(self.index_path, "faiss.index")
        docs_file = os.path.join(self.index_path, "documents.pkl")
        
        faiss.write_index(self.index, index_file)
        
        with open(docs_file, 'wb') as f:
            pickle.dump(self.documents, f)
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text chunks
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        embeddings = self.embeddings.embed_documents(texts)
        return embeddings
    
    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict],
        document_id: int
    ) -> None:
        """
        Add documents to FAISS index.
        
        Args:
            texts: List of text chunks
            metadatas: List of metadata dicts for each chunk
            document_id: Database document ID
        """
        if not texts:
            return
        
        # Generate embeddings
        embeddings = self.generate_embeddings(texts)
        vectors = np.array(embeddings).astype('float32')
        
        # Add to FAISS index
        self.index.add(vectors)
        
        # Store metadata
        start_idx = len(self.documents)
        for i, (text, metadata) in enumerate(zip(texts, metadatas)):
            doc_meta = {
                "id": start_idx + i,
                "text": text,
                "document_id": document_id,
                **metadata
            }
            self.documents.append(doc_meta)
        
        # Save to disk
        self._save_index()
        print(f"Added {len(texts)} chunks to FAISS index")
    
    def search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Tuple[str, Dict, float]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of tuples (text, metadata, distance)
        """
        if self.index.ntotal == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)
        query_vector = np.array([query_embedding]).astype('float32')
        
        # Search
        distances, indices = self.index.search(query_vector, top_k)
        
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.documents):
                doc = self.documents[idx]
                results.append((
                    doc["text"],
                    {k: v for k, v in doc.items() if k != "text"},
                    float(distance)
                ))
        
        return results
    
    def delete_document(self, document_id: int) -> bool:
        """
        Delete all chunks belonging to a document.
        Note: FAISS doesn't support direct deletion, so we rebuild the index.
        
        Args:
            document_id: Database document ID
            
        Returns:
            True if successful
        """
        # Filter out documents to delete
        docs_to_keep = [
            doc for doc in self.documents 
            if doc.get("document_id") != document_id
        ]
        
        if len(docs_to_keep) == len(self.documents):
            return False  # Nothing to delete
        
        # Rebuild index
        self.index = faiss.IndexFlatL2(self.dimension)
        
        if docs_to_keep:
            # Re-embed and add remaining documents
            texts = [doc["text"] for doc in docs_to_keep]
            embeddings = self.generate_embeddings(texts)
            vectors = np.array(embeddings).astype('float32')
            self.index.add(vectors)
        
        # Update documents list and reassign IDs
        self.documents = []
        for i, doc in enumerate(docs_to_keep):
            doc["id"] = i
            self.documents.append(doc)
        
        self._save_index()
        return True
    
    def get_stats(self) -> Dict:
        """Get vector store statistics."""
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "total_documents": len(set(
                doc.get("document_id") for doc in self.documents
            )),
            "dimension": self.dimension,
        }


# Global embedding service instance
embedding_service = EmbeddingService()
