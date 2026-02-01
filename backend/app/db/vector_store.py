# filepath: backend/app/db/vector_store.py
"""
Vector Store for Job Embeddings

This module provides vector storage and similarity search capabilities
for job postings. Uses in-memory storage with numpy for hackathon demo,
but can be extended to use pgvector, Pinecone, or ChromaDB for production.
"""
from typing import List, Dict, Optional, Tuple
import numpy as np
from app.schemas.job import JobPosting
from app.core.embeddings import get_embedding_service


class VectorStore:
    """
    In-memory vector store for job embeddings.
    For production, this would be backed by pgvector, Pinecone, or ChromaDB.
    """
    
    def __init__(self):
        self.embeddings: Dict[str, np.ndarray] = {}  # job_id -> embedding
        self.metadata: Dict[str, dict] = {}  # job_id -> job data
        self.embedding_service = get_embedding_service()
    
    async def add_job(self, job: dict) -> None:
        """Add a job to the vector store."""
        job_id = str(job.get("id", ""))
        if not job_id:
            return
        
        # Generate embedding
        job_text = self.embedding_service.job_to_text(job)
        embedding = await self.embedding_service.get_embedding(job_text)
        
        self.embeddings[job_id] = embedding
        self.metadata[job_id] = job
    
    async def add_jobs_batch(self, jobs: List[dict]) -> None:
        """Add multiple jobs to the vector store."""
        for job in jobs:
            await self.add_job(job)
    
    async def search_similar(
        self, 
        query_embedding: np.ndarray, 
        top_k: int = 10,
        threshold: float = 0.3
    ) -> List[Tuple[dict, float]]:
        """
        Search for similar jobs using cosine similarity.
        Returns list of (job, similarity_score) tuples.
        """
        if not self.embeddings:
            return []
        
        results = []
        for job_id, embedding in self.embeddings.items():
            similarity = self.embedding_service.cosine_similarity(query_embedding, embedding)
            if similarity >= threshold:
                results.append((self.metadata[job_id], similarity))
        
        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    async def search_by_profile(
        self, 
        profile: dict, 
        top_k: int = 10,
        threshold: float = 0.3
    ) -> List[Tuple[dict, float]]:
        """
        Search for jobs similar to a student profile.
        """
        profile_text = self.embedding_service.profile_to_text(profile)
        profile_embedding = await self.embedding_service.get_embedding(profile_text)
        return await self.search_similar(profile_embedding, top_k, threshold)
    
    def clear(self) -> None:
        """Clear all stored embeddings."""
        self.embeddings.clear()
        self.metadata.clear()


# Singleton instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get the singleton vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


async def search_relevant_jobs(query: str, limit: int = 5) -> List[dict]:
    """
    Search for relevant jobs based on a text query.
    Uses embeddings for semantic search.
    """
    store = get_vector_store()
    embedding_service = get_embedding_service()
    
    # Generate query embedding
    query_embedding = await embedding_service.get_embedding(query)
    
    # Search similar jobs
    results = await store.search_similar(query_embedding, top_k=limit)
    
    return [job for job, score in results]
