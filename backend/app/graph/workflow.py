from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.graph.nodes.job_fetcher import fetch_jobs_node
from app.graph.nodes.personalizer import personalize_node
from app.graph.nodes.evidence_mapper import map_evidence_node
from app.graph.nodes.safety_checker import safety_check_node
from app.graph.nodes.applicator import apply_node


def should_start_applying(state: AgentState) -> str:
    """Check if we have jobs to apply to after fetching"""
    job_queue = state.get("job_queue", [])
    if not job_queue or len(job_queue) == 0:
        return "end"
    return "continue"


def should_continue(state: AgentState) -> str:
    """Decide whether to continue applying or end"""
    
    kill_switch = state.get("kill_switch", False)
    if kill_switch:
        return "end"
    
    job_queue = state.get("job_queue", [])
    current_index = state.get("current_job_index", 0)
    
    if current_index >= len(job_queue):
        return "end"
    
    policy = state.get("apply_policy", {})
    applications = state.get("applications_submitted", [])
    
    max_per_day = policy.get("max_applications_per_day", 50)
    successful_apps = [a for a in applications if a.get("status") == "submitted"]
    
    if len(successful_apps) >= max_per_day:
        return "end"
    
    return "continue"


def should_apply(state: AgentState) -> str:
    """Check if current job passes safety check"""
    
    # Check if safety check failed
    errors = state.get("errors", [])
    if any("safety" in e.lower() or "blocked" in e.lower() for e in errors[-3:]):
        return "skip"
    
    return "apply"


async def skip_job_node(state: AgentState) -> dict:
    """Skip current job and move to next"""
    current_index = state.get("current_job_index", 0)
    job_queue = state.get("job_queue", [])
    
    job_title = "Unknown"
    company = "Unknown"
    if current_index < len(job_queue):
        job = job_queue[current_index]
        job_title = job.get("title", "Unknown")
        company = job.get("company", "Unknown")
    
    return {
        "current_job_index": current_index + 1,
        "logs": [f"⏭️ Skipped {job_title} at {company} (safety check failed)"]
    }


def build_workflow() -> StateGraph:
    """Build the complete autonomous job application workflow"""
    
    workflow = StateGraph(AgentState)
    
    # Add all nodes
    workflow.add_node("fetch_jobs", fetch_jobs_node)
    workflow.add_node("personalize", personalize_node)
    workflow.add_node("map_evidence", map_evidence_node)
    workflow.add_node("safety_check", safety_check_node)
    workflow.add_node("apply", apply_node)
    workflow.add_node("skip_job", skip_job_node)
    
    # Set entry point
    workflow.set_entry_point("fetch_jobs")
    
    # After fetching jobs, check if we have any to apply
    workflow.add_conditional_edges(
        "fetch_jobs",
        should_start_applying,
        {
            "continue": "personalize",
            "end": END
        }
    )
    
    # After personalizing, map evidence
    workflow.add_edge("personalize", "map_evidence")
    
    # After evidence mapping, run safety check
    workflow.add_edge("map_evidence", "safety_check")
    
    # After safety check, decide to apply or skip
    workflow.add_conditional_edges(
        "safety_check",
        should_apply,
        {
            "apply": "apply",
            "skip": "skip_job"
        }
    )
    
    # After skipping, check if we should continue
    workflow.add_conditional_edges(
        "skip_job",
        should_continue,
        {
            "continue": "personalize",
            "end": END
        }
    )
    
    # After applying, decide to continue or end
    workflow.add_conditional_edges(
        "apply",
        should_continue,
        {
            "continue": "personalize",
            "end": END
        }
    )
    
    return workflow.compile()


# Compiled workflow instance
app_workflow = build_workflow()
