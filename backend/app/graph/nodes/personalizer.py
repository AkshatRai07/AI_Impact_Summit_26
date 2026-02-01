from app.graph.state import AgentState
from app.core.llm import llm
from langchain_core.messages import HumanMessage, SystemMessage
import json
from typing import List, Dict


TAILORED_RESUME_PROMPT = """You are an expert resume tailoring assistant. Given a student's profile and a job posting, create a tailored resume that highlights the most relevant experience.

CRITICAL RULES:
1. ONLY use information from the student profile - NEVER invent experience, skills, or metrics
2. You may REORDER bullets to prioritize relevance
3. You may REPHRASE bullets slightly to use keywords from the job description, but KEEP the same meaning
4. You may OMIT less relevant bullets if the resume is too long
5. NEVER add skills the student doesn't have
6. NEVER inflate metrics or achievements

Student Profile:
{student_profile}

Job Posting:
Title: {job_title}
Company: {company}
Description: {job_description}
Requirements: {requirements}

Create a tailored resume as JSON with this structure:
{{
    "summary": "2-3 sentence professional summary tailored to this role (using only facts from profile)",
    "relevant_skills": ["skills from profile that match job requirements"],
    "experience": [
        {{
            "company": "string",
            "role": "string",
            "duration": "string",
            "bullets": ["reordered/rephrased bullets prioritizing relevance to this job"]
        }}
    ],
    "projects": [
        {{
            "name": "string",
            "description": "string",
            "technologies": ["string"],
            "bullets": ["relevant bullets"]
        }}
    ],
    "education": "same as profile"
}}

Return ONLY valid JSON."""


COVER_LETTER_PROMPT = """Write a concise, professional cover letter paragraph (3-4 sentences) for this job application.

CRITICAL RULES:
1. ONLY reference experience, projects, and skills from the student profile
2. NEVER invent or exaggerate achievements
3. Be specific - mention actual project names, companies, or metrics from the profile
4. Connect student's experience directly to job requirements

Student Profile:
{student_profile}

Job:
Title: {job_title}
Company: {company}
Description: {job_description}

Write a compelling but TRUTHFUL cover letter paragraph. Return only the paragraph text, no JSON."""


async def personalize_node(state: AgentState) -> dict:
    """
    Generate personalized application materials for current job.
    Uses bullet_bank and proof_pack for grounding - NEVER invents.
    """
    
    job_queue = state.get("job_queue", [])
    current_index = state.get("current_job_index", 0)
    student_profile = state.get("student_profile", {})
    bullet_bank = state.get("bullet_bank", [])
    proof_pack = state.get("proof_pack", [])
    answer_library = state.get("answer_library", {})
    
    if current_index >= len(job_queue):
        return {"errors": ["No more jobs in queue"]}
    
    current_job = job_queue[current_index]
    job_title = current_job.get("title", "")
    company = current_job.get("company", "")
    job_description = current_job.get("description", "")
    job_requirements = current_job.get("requirements", [])
    
    # Format bullet bank for LLM
    bullet_bank_text = "\n".join([
        f"- [{b.get('id')}] {b.get('text')} (from: {b.get('source_name')}, skills: {', '.join(b.get('skills_demonstrated', []))})"
        for b in bullet_bank
    ])
    
    # Format proof pack
    proof_pack_text = "\n".join([
        f"- [{p.get('type')}] {p.get('title')}: {p.get('url')} - {p.get('description')}"
        for p in proof_pack
    ])
    
    system_prompt = """You are a resume tailoring assistant. You help personalize applications while following strict rules:

CRITICAL RULES:
1. ONLY use information from the provided student profile and bullet bank
2. NEVER invent achievements, metrics, or experiences
3. You can REPHRASE bullets but cannot change facts
4. Select the MOST RELEVANT bullets for this specific job
5. Map each job requirement to specific evidence from the bullet bank or proof pack

You must return a JSON object with:
{
    "tailored_resume_sections": {
        "summary": "A 2-3 sentence summary highlighting relevant experience for THIS role",
        "selected_bullets": ["bullet_id1", "bullet_id2", ...],
        "skills_to_highlight": ["skill1", "skill2", ...]
    },
    "cover_letter": "A short 3-4 sentence recruiter note. Be specific about why this candidate fits THIS role. Reference specific projects or achievements.",
    "requirement_evidence_map": [
        {
            "requirement": "the job requirement",
            "evidence": "specific bullet or proof that demonstrates this",
            "evidence_source": "bullet_id or proof_pack item",
            "confidence": "strong|moderate|weak"
        }
    ]
}"""

    user_prompt = f"""Personalize application for:

JOB: {job_title} at {company}

JOB DESCRIPTION:
{job_description}

JOB REQUIREMENTS:
{json.dumps(job_requirements, indent=2)}

STUDENT PROFILE:
{json.dumps(student_profile, indent=2)}

BULLET BANK (use these IDs):
{bullet_bank_text}

PROOF PACK (linkable evidence):
{proof_pack_text}

Create a tailored application package. Only use bullets and facts from above."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    try:
        response = await llm.ainvoke(messages)
        content = response.content.strip()
        
        # Parse JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        personalization = json.loads(content)
        
        return {
            "current_job": current_job,
            "tailored_resume": personalization.get("tailored_resume_sections", {}),
            "tailored_cover_letter": personalization.get("cover_letter", ""),
            "evidence_mapping": personalization.get("requirement_evidence_map", []),
            "logs": [f"📝 Personalized application for {job_title} at {company}"]
        }
        
    except Exception as e:
        return {
            "current_job": current_job,
            "tailored_resume": {},
            "tailored_cover_letter": "",
            "evidence_mapping": [],
            "errors": [f"Personalization failed: {str(e)}"],
            "logs": [f"⚠️ Personalization failed for {job_title}: {str(e)}"]
        }
