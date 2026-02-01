from pydantic import BaseModel, Field
from typing import List, Optional, Any

class JobPosting(BaseModel):
    id: str
    title: str
    company: str
    description: str
    requirements: List[str] = Field(default_factory=list)
    location: str = ""
    remote: Optional[bool] = None
    salary: Optional[str] = None
    
    class Config:
        extra = "ignore"  # Ignore extra fields from sandbox
