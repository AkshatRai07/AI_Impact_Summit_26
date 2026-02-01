import asyncio
from datetime import datetime
from app.tools.sandbox_api import SandboxAPIClient
from app.graph.state import AgentState
from app.db.tracker import ApplicationTracker
from app.api.deps import manager

sandbox_client = SandboxAPIClient()
tracker = ApplicationTracker()

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

async def apply_node(state: AgentState) -> dict:
    """
    Submit application to sandbox with retry logic.
    Handles failures, rate limiting, and tracks all attempts.
    """
    
    # CHECK KILL SWITCH
    if state.get("kill_switch", False):
        return {
            "current_job_index": len(state.get("job_queue", [])),  # Skip to end
            "logs": ["🛑 KILL SWITCH ACTIVATED - Stopping applications"]
        }
    
    current_job = state.get("current_job", {})
    student_profile = state.get("student_profile", {})
    tailored_resume = state.get("tailored_resume", {})
    cover_letter = state.get("tailored_cover_letter", "")
    evidence_mapping = state.get("evidence_mapping", [])
    user_id = state.get("user_id", "demo_user")
    current_index = state.get("current_job_index", 0)
    
    job_id = current_job.get("id", "")
    job_title = current_job.get("title", "Unknown")
    company = current_job.get("company", "Unknown")
    
    if not job_id:
        return {
            "current_job_index": current_index + 1,
            "errors": ["No job ID found"],
            "logs": ["❌ Cannot apply - no job ID"]
        }
    
    # Build application payload
    # Construct resume text from profile + tailored sections
    resume_text = build_resume_text(student_profile, tailored_resume)
    
    payload = {
        "job_id": job_id,
        "applicant_name": student_profile.get("name", "Student"),
        "applicant_email": student_profile.get("email", "student@example.com"),
        "resume": resume_text,
        "cover_letter": cover_letter
    }
    
    # Retry loop
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            # Submit to sandbox
            result = await sandbox_client.submit_application(payload)
            
            confirmation_id = result.get("confirmation_id") or result.get("application_id") or f"conf_{job_id}"
            
            # Track successful submission
            application_record = {
                "job_id": job_id,
                "job_title": job_title,
                "company": company,
                "status": "submitted",
                "confirmation_id": confirmation_id,
                "submitted_at": datetime.utcnow().isoformat(),
                "error_message": None,
                "retry_count": attempt,
                "tailored_resume": tailored_resume,
                "cover_letter": cover_letter,
                "evidence_mapping": evidence_mapping
            }
            
            # Save to tracker
            tracker.add_application(user_id, application_record)
            
            # Broadcast update via WebSocket
            try:
                await manager.broadcast({
                    "type": "application_submitted",
                    "job_id": job_id,
                    "job_title": job_title,
                    "company": company,
                    "status": "submitted",
                    "confirmation_id": confirmation_id
                })
            except:
                pass  # Don't fail if broadcast fails
            
            return {
                "applications_submitted": [application_record],
                "current_job_index": current_index + 1,
                "logs": [f"✅ Applied to {job_title} at {company} (Confirmation: {confirmation_id})"]
            }
            
        except Exception as e:
            last_error = str(e)
            
            # Check if it's a duplicate application (already applied)
            if "duplicate" in last_error.lower() or "already applied" in last_error.lower() or "409" in last_error:
                # Mark as already applied, not failed
                already_applied_record = {
                    "job_id": job_id,
                    "job_title": job_title,
                    "company": company,
                    "status": "already_applied",
                    "confirmation_id": None,
                    "submitted_at": datetime.utcnow().isoformat(),
                    "error_message": "Already applied to this job",
                    "retry_count": 0,
                    "tailored_resume": tailored_resume,
                    "cover_letter": cover_letter,
                    "evidence_mapping": evidence_mapping
                }
                
                tracker.add_application(user_id, already_applied_record)
                
                return {
                    "applications_submitted": [already_applied_record],
                    "current_job_index": current_index + 1,
                    "logs": [f"⏭️ Already applied to {job_title} at {company}, skipping"]
                }
            
            # Check if rate limited
            if "rate" in last_error.lower() or "429" in last_error:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
            elif attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY)
            
            continue
    
    # All retries failed
    failed_record = {
        "job_id": job_id,
        "job_title": job_title,
        "company": company,
        "status": "failed",
        "confirmation_id": None,
        "submitted_at": datetime.utcnow().isoformat(),
        "error_message": last_error,
        "retry_count": MAX_RETRIES,
        "tailored_resume": tailored_resume,
        "cover_letter": cover_letter,
        "evidence_mapping": evidence_mapping
    }
    
    tracker.add_application(user_id, failed_record)
    
    try:
        await manager.broadcast({
            "type": "application_failed",
            "job_id": job_id,
            "job_title": job_title,
            "company": company,
            "status": "failed",
            "error": last_error
        })
    except:
        pass
    
    return {
        "applications_submitted": [failed_record],
        "current_job_index": current_index + 1,
        "errors": [f"Failed to apply to {job_title} after {MAX_RETRIES} attempts: {last_error}"],
        "logs": [f"❌ Failed to apply to {job_title} at {company}: {last_error}"]
    }


def build_resume_text(profile: dict, tailored: dict) -> str:
    """Build resume text from profile and tailored sections"""
    
    name = profile.get("name", "")
    email = profile.get("email", "")
    phone = profile.get("phone", "")
    
    lines = [name, email, phone, ""]
    
    # Summary
    summary = tailored.get("summary") or profile.get("summary", "")
    if summary:
        lines.extend(["SUMMARY", summary, ""])
    
    # Skills - handle both list and dict formats
    skills = profile.get("skills", [])
    skills_to_highlight = tailored.get("skills_to_highlight", [])
    all_skills = []
    
    if isinstance(skills, dict):
        # Dict format: {"languages": [...], "frameworks": [...], ...}
        for category in ["languages", "frameworks", "tools", "other"]:
            all_skills.extend(skills.get(category, []))
    elif isinstance(skills, list):
        # List format: ["Python", "JavaScript", ...]
        all_skills = skills
    
    # Prioritize highlighted skills
    if skills_to_highlight:
        ordered_skills = skills_to_highlight + [s for s in all_skills if s not in skills_to_highlight]
    else:
        ordered_skills = all_skills
    
    if ordered_skills:
        lines.extend(["SKILLS", ", ".join(ordered_skills[:15]), ""])
    
    # Experience
    experience = profile.get("experience", [])
    if experience:
        lines.append("EXPERIENCE")
        for exp in experience:
            lines.append(f"{exp.get('title', '')} at {exp.get('company', '')} ({exp.get('start_date', '')} - {exp.get('end_date', 'Present')})")
            for bullet in exp.get("bullets", []):
                lines.append(f"  • {bullet}")
            lines.append("")
    
    # Projects
    projects = profile.get("projects", [])
    if projects:
        lines.append("PROJECTS")
        for proj in projects:
            lines.append(f"{proj.get('name', '')} - {', '.join(proj.get('technologies', []))}")
            if proj.get("url"):
                lines.append(f"  {proj.get('url')}")
            for bullet in proj.get("bullets", []):
                lines.append(f"  • {bullet}")
            lines.append("")
    
    # Education
    education = profile.get("education", [])
    if education:
        lines.append("EDUCATION")
        for edu in education:
            lines.append(f"{edu.get('degree', '')} in {edu.get('field', '')} - {edu.get('institution', '')} ({edu.get('graduation_date', '')})")
            if edu.get("gpa"):
                lines.append(f"  GPA: {edu.get('gpa')}")
            lines.append("")
    
    return "\n".join(lines)
