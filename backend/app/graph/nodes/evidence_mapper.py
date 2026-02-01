from app.graph.state import AgentState


async def map_evidence_node(state: AgentState) -> dict:
    """
    Validates and enriches evidence mapping.
    Ensures every claim is grounded in the student's actual data.
    """
    
    evidence_mapping = state.get("evidence_mapping", [])
    bullet_bank = state.get("bullet_bank", [])
    proof_pack = state.get("proof_pack", [])
    current_job = state.get("current_job", {})
    
    job_title = current_job.get("title", "Unknown")
    
    # Create lookup maps
    bullet_lookup = {b.get("id"): b for b in bullet_bank}
    proof_lookup = {p.get("url"): p for p in proof_pack}
    
    enriched_mapping = []
    
    for mapping in evidence_mapping:
        requirement = mapping.get("requirement", "")
        evidence = mapping.get("evidence", "")
        source = mapping.get("evidence_source", "")
        confidence = mapping.get("confidence", "weak")
        
        enriched = {
            "requirement": requirement,
            "evidence": evidence,
            "evidence_source": source,
            "confidence": confidence,
            "grounded": False,
            "source_details": None
        }
        
        # Check if grounded in bullet bank
        if source in bullet_lookup:
            enriched["grounded"] = True
            enriched["source_details"] = {
                "type": "bullet",
                "source_name": bullet_lookup[source].get("source_name"),
                "category": bullet_lookup[source].get("category")
            }
        # Check if grounded in proof pack
        elif source in proof_lookup:
            enriched["grounded"] = True
            enriched["source_details"] = {
                "type": "proof",
                "title": proof_lookup[source].get("title"),
                "url": source
            }
        # Partial match check
        else:
            for bid, bullet in bullet_lookup.items():
                if evidence.lower() in bullet.get("text", "").lower():
                    enriched["grounded"] = True
                    enriched["evidence_source"] = bid
                    enriched["source_details"] = {
                        "type": "bullet",
                        "source_name": bullet.get("source_name"),
                        "matched_by": "text_similarity"
                    }
                    break
        
        enriched_mapping.append(enriched)
    
    grounded_count = sum(1 for m in enriched_mapping if m.get("grounded"))
    total_count = len(enriched_mapping)
    
    return {
        "evidence_mapping": enriched_mapping,
        "logs": [f"📋 Evidence mapped for {job_title}: {grounded_count}/{total_count} claims grounded"]
    }
