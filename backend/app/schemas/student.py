from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class Bullet(BaseModel):
    """A single achievement bullet tied to a specific experience/project"""
    text: str
    source: str  # e.g., "Internship at Google", "Project: ChatBot"
    metrics: Optional[str] = None  # e.g., "40% improvement"
    skills_demonstrated: List[str] = Field(default_factory=list)

class ProofItem(BaseModel):
    """A link or artifact that backs up a claim"""
    title: str
    url: str
    description: str
    related_to: str  # Which experience/project this proves

class ExperienceItem(BaseModel):
    company: str
    role: str
    duration: str
    description: str
    bullets: List[str] = Field(default_factory=list)

class ProjectItem(BaseModel):
    name: str
    description: str
    technologies: List[str] = Field(default_factory=list)
    url: Optional[str] = None
    bullets: List[str] = Field(default_factory=list)

class EducationItem(BaseModel):
    institution: str
    degree: str
    field: str
    graduation_date: str
    gpa: Optional[str] = None

class Constraints(BaseModel):
    """Student's job search constraints"""
    locations: List[str] = Field(default_factory=list)  # Preferred locations
    remote_preference: str = "flexible"  # "remote_only", "hybrid", "onsite", "flexible"
    visa_required: bool = False
    work_authorization: str = ""  # e.g., "US Citizen", "F1-OPT", "H1B Required"
    earliest_start_date: Optional[str] = None
    salary_expectation: Optional[str] = None

class AnswerLibrary(BaseModel):
    """Reusable answers for common application questions"""
    work_authorization: str = ""
    availability: str = ""
    relocation: str = ""
    salary_expectations: str = ""
    why_interested: str = ""  # Generic "why this field" answer
    greatest_strength: str = ""
    custom_answers: Dict[str, str] = Field(default_factory=dict)

class StudentProfile(BaseModel):
    """The complete student artifact pack - source of truth"""
    # Basic Info
    full_name: str
    email: str
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    
    # Core Content
    education: List[EducationItem] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    
    # Artifact Pack Components (NEW)
    bullet_bank: List[Bullet] = Field(default_factory=list)
    proof_pack: List[ProofItem] = Field(default_factory=list)
    answer_library: AnswerLibrary = Field(default_factory=AnswerLibrary)
    constraints: Constraints = Field(default_factory=Constraints)
    
    # Raw data for reference
    raw_text: str = ""
