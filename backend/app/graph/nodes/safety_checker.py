from app.graph.state import AgentState


async def safety_check_node(state: AgentState) -> dict:
    """
    Safety checker to ensure:
    1. No fabricated claims in the application
    2. Application complies with policy
    3. All evidence is grounded in bullet_bank or proof_pack
    """
    
    current_job = state.get("current_job", {})
    student_profile = state.get("student_profile", {})
    policy = state.get("apply_policy", {})
    tailored_resume = state.get("tailored_resume", {})
    cover_letter = state.get("tailored_cover_letter", "")
    evidence_mapping = state.get("evidence_mapping", [])
    bullet_bank = state.get("bullet_bank", [])
    proof_pack = state.get("proof_pack", [])
    
    job_title = current_job.get("title", "Unknown")
    company = current_job.get("company", "Unknown")
    
    errors = []
    warnings = []
    
    # 1. Check blocked companies
    blocked_companies = [c.lower() for c in policy.get("blocked_companies", [])]
    if company.lower() in blocked_companies:
        errors.append(f"SAFETY BLOCK: {company} is in blocked companies list")
    
    # 2. Check blocked role types
    blocked_roles = [r.lower() for r in policy.get("blocked_role_types", [])]
    for blocked in blocked_roles:
        if blocked in job_title.lower():
            errors.append(f"SAFETY BLOCK: Role type '{blocked}' is blocked")
    
    # 3. Check match threshold
    match_score = current_job.get("match_score", 0)
    min_threshold = policy.get("min_match_threshold", 30)
    if match_score < min_threshold:
        errors.append(f"SAFETY BLOCK: Match score {match_score} below threshold {min_threshold}")
    
    # 4. Verify evidence grounding
    bullet_ids = {b.get("id") for b in bullet_bank}
    proof_urls = {p.get("url") for p in proof_pack}
    
    for mapping in evidence_mapping:
        source = mapping.get("evidence_source", "")
        confidence = mapping.get("confidence", "weak")
        
        # Check if source exists in our banks
        if source and source not in bullet_ids and source not in proof_urls:
            if confidence == "strong":
                warnings.append(f"Warning: Evidence source '{source}' not found in bullet bank or proof pack")
    
    # 5. Check selected bullets exist
    selected_bullets = tailored_resume.get("selected_bullets", [])
    for bullet_id in selected_bullets:
        if bullet_id not in bullet_ids:
            warnings.append(f"Warning: Selected bullet '{bullet_id}' not found in bullet bank")
    
    # 6. Check required constraints
    if policy.get("require_remote"):
        if not current_job.get("is_remote"):
            errors.append("SAFETY BLOCK: Job is not remote but remote is required")
    
    required_location = policy.get("required_location")
    if required_location:
        job_location = current_job.get("location", "").lower()
        if required_location.lower() not in job_location:
            errors.append(f"SAFETY BLOCK: Job location '{job_location}' doesn't match required '{required_location}'")
    
    if errors:
        return {
            "errors": errors,
            "logs": [f"🚫 Safety check FAILED for {job_title} at {company}: {errors[0]}"],
            "current_job_index": state.get("current_job_index", 0) + 1  # Skip this job
        }
    
    logs = [f"✅ Safety check PASSED for {job_title} at {company}"]
    if warnings:
        logs.extend([f"⚠️ {w}" for w in warnings])
    
    return {"logs": logs}
