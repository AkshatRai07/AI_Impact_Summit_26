# filepath: backend/app/core/embeddings.py
"""
Vector Embedding Service for Semantic Job Matching

Uses Google's Gemini embedding model for generating embeddings and 
computing cosine similarity between student profiles and job descriptions.
This enables semantic matching beyond simple keyword overlap.
"""
import numpy as np
from typing import List, Dict, Optional, Tuple
from functools import lru_cache
import asyncio
import google.generativeai as genai
from app.core.config import settings

# Configure the Gemini API
genai.configure(api_key=settings.GOOGLE_API_KEY)


class EmbeddingService:
    """
    Service for generating embeddings and computing semantic similarity.
    Uses Gemini's text-embedding model for high-quality embeddings.
    """
    
    def __init__(self, model_name: str = "models/text-embedding-004"):
        self.model_name = model_name
        self._embedding_cache: Dict[str, np.ndarray] = {}
    
    def _get_embedding_sync(self, text: str) -> np.ndarray:
        """Synchronous embedding generation with caching."""
        # Check cache first
        cache_key = hash(text[:500])  # Use first 500 chars for cache key
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]
        
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document"
            )
            embedding = np.array(result['embedding'])
            
            # Cache the result (limit cache size)
            if len(self._embedding_cache) < 1000:
                self._embedding_cache[cache_key] = embedding
            
            return embedding
        except Exception as e:
            print(f"[EMBEDDING ERROR] Failed to generate embedding: {e}")
            # Return zero vector as fallback
            return np.zeros(768)
    
    async def get_embedding(self, text: str) -> np.ndarray:
        """Async wrapper for embedding generation."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_embedding_sync, text)
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts efficiently."""
        # Process in parallel with rate limiting
        tasks = [self.get_embedding(text) for text in texts]
        return await asyncio.gather(*tasks)
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
    
    def profile_to_text(self, profile: dict) -> str:
        """
        Convert a student profile to a rich text representation for embedding.
        This captures the semantic essence of the candidate.
        """
        parts = []
        
        # Personal info
        if profile.get("name"):
            parts.append(f"Candidate: {profile['name']}")
        
        # Skills - most important for matching
        skills = profile.get("skills", {})
        if isinstance(skills, dict):
            all_skills = []
            all_skills.extend(skills.get("languages", []))
            all_skills.extend(skills.get("frameworks", []))
            all_skills.extend(skills.get("tools", []))
            all_skills.extend(skills.get("other", []))
            if all_skills:
                parts.append(f"Technical skills: {', '.join(all_skills)}")
        elif isinstance(skills, list):
            parts.append(f"Technical skills: {', '.join(skills)}")
        
        # Experience
        experience = profile.get("experience", [])
        for exp in experience[:3]:  # Top 3 experiences
            title = exp.get("title", exp.get("role", ""))
            company = exp.get("company", "")
            description = exp.get("description", "")
            if title or company:
                parts.append(f"Work experience: {title} at {company}. {description[:200]}")
        
        # Education
        education = profile.get("education", [])
        for edu in education[:2]:  # Top 2 education entries
            degree = edu.get("degree", "")
            field = edu.get("field", "")
            institution = edu.get("institution", edu.get("school", ""))
            if degree or field:
                parts.append(f"Education: {degree} in {field} from {institution}")
        
        # Projects
        projects = profile.get("projects", [])
        for proj in projects[:3]:  # Top 3 projects
            name = proj.get("name", "")
            description = proj.get("description", "")
            tech = proj.get("technologies", [])
            if name:
                tech_str = f" using {', '.join(tech)}" if tech else ""
                parts.append(f"Project: {name}{tech_str}. {description[:150]}")
        
        # Preferences/Constraints
        constraints = profile.get("constraints", {})
        if constraints.get("preferred_locations"):
            parts.append(f"Preferred locations: {', '.join(constraints['preferred_locations'])}")
        if constraints.get("open_to_remote"):
            parts.append("Open to remote work")
        
        return " ".join(parts)
    
    def job_to_text(self, job: dict) -> str:
        """
        Convert a job posting to a rich text representation for embedding.
        """
        parts = []
        
        # Title and company - core identity
        title = job.get("title", "")
        company = job.get("company", "")
        parts.append(f"Job: {title} at {company}")
        
        # Description
        description = job.get("description", "")
        if description:
            parts.append(f"Description: {description[:500]}")
        
        # Requirements
        requirements = job.get("requirements", [])
        if isinstance(requirements, list):
            parts.append(f"Requirements: {', '.join(requirements)}")
        elif isinstance(requirements, str):
            parts.append(f"Requirements: {requirements}")
        
        # Location and remote
        location = job.get("location", "")
        is_remote = job.get("is_remote", job.get("remote", False))
        location_str = f"Location: {location}"
        if is_remote:
            location_str += " (Remote available)"
        parts.append(location_str)
        
        # Experience level
        exp_years = job.get("experience_required", job.get("experience_years", 0))
        if exp_years:
            parts.append(f"Experience required: {exp_years} years")
        
        # Salary if available
        salary = job.get("salary", job.get("salary_range", ""))
        if salary:
            parts.append(f"Salary: {salary}")
        
        return " ".join(parts)
    
    async def compute_match_score(
        self, 
        profile: dict, 
        job: dict,
        profile_embedding: Optional[np.ndarray] = None
    ) -> Tuple[float, str]:
        """
        Compute semantic match score between a profile and job.
        Returns (score 0-100, explanation).
        """
        # Generate embeddings
        profile_text = self.profile_to_text(profile)
        job_text = self.job_to_text(job)
        
        if profile_embedding is None:
            profile_embedding = await self.get_embedding(profile_text)
        job_embedding = await self.get_embedding(job_text)
        
        # Compute cosine similarity (-1 to 1, typically 0 to 1 for similar content)
        similarity = self.cosine_similarity(profile_embedding, job_embedding)
        
        # Convert to 0-100 score (similarity is usually 0.3-0.9 for related content)
        # Map 0.3-0.9 to 20-100
        normalized_score = max(0, min(100, (similarity - 0.3) * (80 / 0.6) + 20))
        
        # Generate explanation based on score
        if normalized_score >= 80:
            explanation = f"🎯 Excellent semantic match ({similarity:.2f})"
        elif normalized_score >= 60:
            explanation = f"✅ Strong semantic match ({similarity:.2f})"
        elif normalized_score >= 40:
            explanation = f"📊 Moderate match ({similarity:.2f})"
        else:
            explanation = f"⚠️ Low semantic match ({similarity:.2f})"
        
        return normalized_score, explanation


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get the singleton embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
