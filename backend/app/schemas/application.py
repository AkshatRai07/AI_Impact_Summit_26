from pydantic import BaseModel
from typing import Optional

class ApplicationPayload(BaseModel):
    job_id: str
    candidate_name: str
    cover_letter: str
    resume_text: str  # The tailored resume

class ApplicationResult(BaseModel):
    success: bool
    status: str
    message: Optional[str] = None
