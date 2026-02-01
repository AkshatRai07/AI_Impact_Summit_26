# filepath: backend/app/api/routes/resume.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from app.tools.pdf_parser import extract_text_from_pdf, parse_resume_to_profile
from app.core.llm import get_llm
from app.schemas.student import StudentProfile
from app.api.deps import get_current_user
from app.db.supabase import supabase
import json
import os
import uuid
import tempfile
from typing import Optional

router = APIRouter(prefix="/resume", tags=["Resume"])

ARTIFACT_EXTRACTION_PROMPT = """You are an expert resume parser. Extract ALL information from the following resume text into a structured format.

CRITICAL RULES:
1. ONLY extract information that is EXPLICITLY stated in the resume
2. DO NOT invent, assume, or embellish any details
3. If information is not present, leave the field empty or use empty arrays
4. For bullets, extract EXACT text from the resume - do not rephrase
5. For metrics/numbers, only include if explicitly stated

Resume Text:
{resume_text}

Extract into this JSON structure:
{{
    "full_name": "string",
    "email": "string",
    "phone": "string or null",
    "linkedin_url": "string or null",
    "github_url": "string or null",
    "portfolio_url": "string or null",
    
    "education": [
        {{
            "institution": "string",
            "degree": "string",
            "field": "string",
            "graduation_date": "string",
            "gpa": "string or null"
        }}
    ],
    
    "experience": [
        {{
            "company": "string",
            "role": "string",
            "duration": "string",
            "description": "string",
            "bullets": ["exact bullet points from resume"]
        }}
    ],
    
    "projects": [
        {{
            "name": "string",
            "description": "string",
            "technologies": ["string"],
            "url": "string or null",
            "bullets": ["exact bullet points from resume"]
        }}
    ],
    
    "skills": ["string"],
    
    "bullet_bank": [
        {{
            "text": "exact achievement bullet from resume",
            "source": "which experience/project this came from",
            "metrics": "any numbers/percentages mentioned, or null",
            "skills_demonstrated": ["skills shown in this bullet"]
        }}
    ],
    
    "proof_pack": [
        {{
            "title": "name of the proof item",
            "url": "the URL from resume",
            "description": "what this proves",
            "related_to": "which experience/project"
        }}
    ],
    
    "answer_library": {{
        "work_authorization": "extract if mentioned, else empty string",
        "availability": "extract if mentioned, else empty string",
        "relocation": "extract if mentioned, else empty string",
        "salary_expectations": "extract if mentioned, else empty string",
        "why_interested": "derive from resume summary/objective if present",
        "greatest_strength": "derive from top achievements if clear",
        "custom_answers": {{}}
    }},
    
    "constraints": {{
        "locations": ["extract preferred locations if mentioned"],
        "remote_preference": "flexible",
        "visa_required": false,
        "work_authorization": "extract if mentioned",
        "earliest_start_date": null,
        "salary_expectation": null
    }}
}}

Return ONLY valid JSON, no markdown or explanation."""


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    user=Depends(get_current_user)
):
    """Upload resume with authentication required"""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    contents = await file.read()
    raw_text = extract_text_from_pdf(contents)  # Now accepts bytes
    
    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from PDF")
    
    llm = get_llm()
    prompt = ARTIFACT_EXTRACTION_PROMPT.format(resume_text=raw_text)
    
    response = await llm.ainvoke(prompt)
    
    # Clean potential markdown wrapper
    content = response.content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1])
    
    try:
        profile_data = json.loads(content)
        profile_data["raw_text"] = raw_text
        return {"success": True, "profile": profile_data}
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to parse LLM response as JSON: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create student profile: {str(e)}"
        )


@router.post("/parse")
async def parse_resume(
    file: UploadFile = File(...),
    linkedin_text: Optional[str] = Form(None),
    github_url: Optional[str] = Form(None),
    portfolio_url: Optional[str] = Form(None),
    additional_projects: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None)
):
    """
    Parse a resume PDF and generate the complete Student Artifact Pack.
    No authentication required for hackathon demo.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Read file content directly
        content = await file.read()
        
        # Extract text from PDF (now accepts bytes)
        resume_text = extract_text_from_pdf(content)
        
        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        
        # Parse with additional info
        additional_info = {
            "linkedin_text": linkedin_text,
            "github_url": github_url,
            "portfolio_url": portfolio_url,
            "additional_projects": additional_projects
        }
        
        # Get complete artifact pack
        artifact_pack = await parse_resume_to_profile(resume_text, additional_info)
        
        # Store in Supabase if user_id provided and supabase is configured
        profile_id = str(uuid.uuid4())
        if user_id and supabase:
            try:
                supabase.table("student_profiles").upsert({
                    "id": profile_id,
                    "user_id": user_id,
                    "student_profile": artifact_pack.get("student_profile", {}),
                    "bullet_bank": artifact_pack.get("bullet_bank", []),
                    "answer_library": artifact_pack.get("answer_library", {}),
                    "proof_pack": artifact_pack.get("proof_pack", []),
                    "raw_resume_text": resume_text
                }).execute()
            except Exception as e:
                print(f"Failed to store in Supabase: {e}")
        
        return {
            "success": True,
            "profile_id": profile_id,
            "artifact_pack": {
                "student_profile": artifact_pack.get("student_profile", {}),
                "bullet_bank": artifact_pack.get("bullet_bank", []),
                "answer_library": artifact_pack.get("answer_library", {}),
                "proof_pack": artifact_pack.get("proof_pack", [])
            },
            "raw_text_length": len(resume_text)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")


@router.get("/profile/{user_id}")
async def get_profile(user_id: str):
    """Get stored artifact pack for a user"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        result = supabase.table("student_profiles").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        profile_data = result.data[0]
        return {
            "success": True,
            "artifact_pack": {
                "student_profile": profile_data.get("student_profile", {}),
                "bullet_bank": profile_data.get("bullet_bank", []),
                "answer_library": profile_data.get("answer_library", {}),
                "proof_pack": profile_data.get("proof_pack", [])
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
