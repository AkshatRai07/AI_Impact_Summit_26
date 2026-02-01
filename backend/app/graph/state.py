from typing import TypedDict, List, Optional, Any, Annotated
from operator import add

class ApplicationRecord(TypedDict, total=False):
    job_id: str
    job_title: str
    company: str
    status: str  # queued, submitted, failed, retried
    confirmation_id: Optional[str]
    submitted_at: Optional[str]
    error_message: Optional[str]
    retry_count: int
    tailored_resume: Optional[dict]
    cover_letter: Optional[str]
    evidence_mapping: Optional[List[dict]]


class AgentState(TypedDict, total=False):
    """Complete state for the autonomous job application agent"""
    
    # User identification
    user_id: str
    
    # Student Artifact Pack (from resume parsing)
    student_profile: dict
    bullet_bank: List[dict]
    answer_library: dict
    proof_pack: List[dict]
    
    # Apply Policy (set by student at onboarding)
    apply_policy: dict  # {max_applications_per_day, min_match_threshold, blocked_companies, blocked_roles, required_remote, required_location, etc.}
    
    # Job Search State
    job_queue: List[dict]  # Ranked jobs ready to apply
    applied_job_ids: List[str]  # Already applied (for deduplication)
    current_job_index: int
    
    # Current Job Processing
    current_job: dict
    match_score: float
    match_reasoning: str
    
    # Personalization Outputs
    tailored_resume: dict  # Modified resume sections
    tailored_cover_letter: str
    evidence_mapping: List[dict]  # requirement -> evidence mappings
    
    # Application Tracking
    applications_submitted: Annotated[List[ApplicationRecord], add]
    
    # Control
    kill_switch: bool
    errors: Annotated[List[str], add]
    logs: Annotated[List[str], add]
    
    # Workflow control
    should_continue: bool
