# filepath: backend/app/graph/nodes/job_fetcher.py
from app.tools.sandbox_api import SandboxAPIClient
from app.graph.state import AgentState
from app.db.tracker import ApplicationTracker
from app.core.embeddings import get_embedding_service
from typing import Optional
import numpy as np

sandbox_client = SandboxAPIClient()
tracker = ApplicationTracker()
embedding_service = get_embedding_service()


def calculate_match_score(job: dict, profile: dict, policy: dict) -> tuple[float, str]:
    """
    Calculate match score and provide explanation.
    Returns (score, explanation)
    """
    score = 0.0
    reasons = []
    
    job_title = job.get("title", "").lower()
    job_description = job.get("description", "").lower()
    job_requirements = job.get("requirements", [])
    if isinstance(job_requirements, str):
        job_requirements = [job_requirements]
    job_location = job.get("location", "").lower()
    job_is_remote = job.get("is_remote", job.get("remote", False))
    job_experience_required = job.get("experience_required", job.get("experience_years", 0))
    if isinstance(job_experience_required, str):
        try:
            job_experience_required = int(job_experience_required.split()[0])
        except:
            job_experience_required = 0
    company = job.get("company", "")
    
    # Get student skills - handle both dict and list formats
    skills = profile.get("skills", {})
    all_skills = []
    if isinstance(skills, dict):
        all_skills.extend([s.lower() for s in skills.get("languages", [])])
        all_skills.extend([s.lower() for s in skills.get("frameworks", [])])
        all_skills.extend([s.lower() for s in skills.get("tools", [])])
        all_skills.extend([s.lower() for s in skills.get("other", [])])
    elif isinstance(skills, list):
        all_skills = [s.lower() for s in skills]
    
    # 1. Skill overlap (40 points max)
    skill_matches = []
    for skill in all_skills:
        if skill in job_description or skill in job_title:
            skill_matches.append(skill)
        for req in job_requirements:
            if isinstance(req, str) and skill in req.lower():
                if skill not in skill_matches:
                    skill_matches.append(skill)
    
    skill_score = min(len(skill_matches) * 8, 40)
    score += skill_score
    if skill_matches:
        reasons.append(f"Skills match: {', '.join(skill_matches[:5])}")
    
    # 2. Experience fit (25 points max)
    experience = profile.get("experience", [])
    total_experience_months = len(experience) * 12  # Rough estimate
    required_years = job_experience_required
    
    if required_years == 0:
        score += 25
        reasons.append("Entry-level position (no experience required)")
    elif total_experience_months >= required_years * 12:
        score += 25
        reasons.append(f"Experience meets requirement ({required_years} years)")
    elif total_experience_months >= required_years * 6:
        score += 15
        reasons.append(f"Some relevant experience (need {required_years} years)")
    else:
        score += 5
        reasons.append(f"Limited experience for this role")
    
    # 3. Location/Remote match (20 points max)
    constraints = profile.get("constraints", {})
    preferred_locations = [loc.lower() for loc in constraints.get("preferred_locations", constraints.get("locations", []))]
    open_to_remote = constraints.get("open_to_remote", constraints.get("remote_preference", "flexible") != "onsite")
    
    if job_is_remote and open_to_remote:
        score += 20
        reasons.append("Remote position matches preference")
    elif any(loc in job_location for loc in preferred_locations):
        score += 20
        reasons.append(f"Location matches: {job_location}")
    elif job_is_remote:
        score += 15
        reasons.append("Remote option available")
    else:
        score += 5
        reasons.append(f"Location: {job_location}")
    
    # 4. Education match (15 points max)
    education = profile.get("education", [])
    edu_keywords = []
    for edu in education:
        if edu.get("field"):
            edu_keywords.append(edu["field"].lower())
        if edu.get("degree"):
            edu_keywords.append(edu["degree"].lower())
    
    edu_match = any(kw in job_description for kw in edu_keywords)
    if edu_match:
        score += 15
        reasons.append("Education background relevant")
    else:
        score += 5
    
    # Policy checks (can disqualify)
    blocked_companies = [c.lower() for c in policy.get("blocked_companies", [])]
    if company.lower() in blocked_companies:
        score = 0
        reasons = ["BLOCKED: Company in blocked list"]
    
    blocked_roles = [r.lower() for r in policy.get("blocked_role_types", [])]
    for blocked in blocked_roles:
        if blocked in job_title:
            score = 0
            reasons = [f"BLOCKED: Role type '{blocked}' in blocked list"]
    
    explanation = " | ".join(reasons) if reasons else "Basic match"
    
    return score, explanation


async def fetch_jobs_node(state: AgentState) -> dict:
    """Fetch jobs from sandbox, deduplicate, and rank them using HYBRID scoring:
    - Semantic similarity via embeddings (60% weight)
    - Rule-based matching (40% weight)
    """
    
    print("[FETCH_JOBS] Starting job fetch with VECTOR SIMILARITY ranking...")
    
    student_profile = state.get("student_profile", {})
    policy = state.get("apply_policy", {})
    user_id = state.get("user_id", "demo_user")
    
    logs = []
    
    # Fetch jobs from sandbox
    try:
        jobs = await sandbox_client.fetch_jobs()
        print(f"[FETCH_JOBS] Fetched {len(jobs)} jobs from sandbox")
        logs.append(f"📥 Fetched {len(jobs)} jobs from sandbox")
    except Exception as e:
        print(f"[FETCH_JOBS ERROR] Failed to fetch jobs: {str(e)}")
        return {
            "errors": [f"Failed to fetch jobs: {str(e)}"],
            "job_queue": [],
            "logs": [f"❌ Failed to fetch jobs: {str(e)}"]
        }
    
    # Get already applied jobs for deduplication
    applied_ids = set(state.get("applied_job_ids", []))
    try:
        tracked = tracker.get_user_applications(user_id)
        for app in tracked:
            applied_ids.add(app.get("job_id"))
    except:
        pass
    
    # Pre-compute profile embedding once for efficiency
    logs.append("🧠 Generating profile embedding for semantic matching...")
    print("[FETCH_JOBS] Generating profile embedding...")
    
    try:
        profile_text = embedding_service.profile_to_text(student_profile)
        profile_embedding = await embedding_service.get_embedding(profile_text)
        logs.append("✅ Profile embedding ready - using vector similarity!")
        use_embeddings = True
    except Exception as e:
        print(f"[FETCH_JOBS] Embedding failed, falling back to rule-based: {e}")
        logs.append(f"⚠️ Embedding unavailable, using rule-based matching")
        profile_embedding = None
        use_embeddings = False
    
    # Filter and rank
    ranked_jobs = []
    
    for job in jobs:
        job_id = str(job.get("id", ""))
        
        # Skip if already applied
        if job_id in applied_ids:
            logs.append(f"⏭️ Skipping {job.get('title', 'Unknown')} - already applied")
            continue
        
        # Check policy blocks first (cheap check)
        company = job.get("company", "")
        job_title = job.get("title", "").lower()
        
        blocked_companies = [c.lower() for c in policy.get("blocked_companies", [])]
        if company.lower() in blocked_companies:
            logs.append(f"🚫 Blocked: {job.get('title')} (company blocked)")
            continue
            
        blocked_roles = [r.lower() for r in policy.get("blocked_role_types", [])]
        is_blocked_role = any(blocked in job_title for blocked in blocked_roles)
        if is_blocked_role:
            logs.append(f"🚫 Blocked: {job.get('title')} (role type blocked)")
            continue
        
        # HYBRID SCORING: Combine semantic + rule-based
        if use_embeddings:
            # Semantic score (60% weight)
            semantic_score, semantic_reason = await embedding_service.compute_match_score(
                student_profile, job, profile_embedding
            )
            
            # Rule-based score (40% weight)
            rule_score, rule_reason = calculate_match_score(job, student_profile, policy)
            
            # Combined score
            combined_score = (semantic_score * 0.6) + (rule_score * 0.4)
            explanation = f"{semantic_reason} | {rule_reason}"
        else:
            # Fallback to pure rule-based
            combined_score, explanation = calculate_match_score(job, student_profile, policy)
        
        # Check minimum threshold
        min_threshold = policy.get("min_match_threshold", 30)
        if combined_score < min_threshold:
            logs.append(f"⏭️ Skipping {job.get('title', 'Unknown')} - score {combined_score:.1f} below threshold {min_threshold}")
            continue
        
        job_with_score = {
            **job,
            "match_score": combined_score,
            "match_reasoning": explanation,
            "semantic_match": use_embeddings
        }
        ranked_jobs.append(job_with_score)
    
    # Sort by score descending
    ranked_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    
    # Apply max limit from policy
    max_per_day = policy.get("max_applications_per_day", 50)
    ranked_jobs = ranked_jobs[:max_per_day]
    
    # Log top matches
    if ranked_jobs:
        top_job = ranked_jobs[0]
        logs.append(f"🏆 Top match: {top_job.get('title')} (score: {top_job.get('match_score', 0):.1f})")
    
    logs.append(f"✅ Apply Queue ready: {len(ranked_jobs)} jobs ranked by semantic similarity")
    print(f"[FETCH_JOBS] Final queue: {len(ranked_jobs)} jobs after filtering")
    
    return {
        "job_queue": ranked_jobs,
        "applied_job_ids": list(applied_ids),
        "current_job_index": 0,
        "logs": logs
    }
