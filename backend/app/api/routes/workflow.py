from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
import asyncio

from app.graph.workflow import app_workflow
from app.graph.state import AgentState
from app.db.tracker import ApplicationTracker

router = APIRouter(prefix="/workflow", tags=["Workflow"])
tracker = ApplicationTracker()

# Store for active workflows (for kill switch)
active_workflows: dict = {}


class ApplyPolicy(BaseModel):
    max_applications_per_day: int = 50
    min_match_threshold: float = 30.0
    blocked_companies: List[str] = []
    blocked_role_types: List[str] = []
    require_remote: bool = False
    required_location: Optional[str] = None


class StartWorkflowRequest(BaseModel):
    user_id: str
    student_profile: dict
    bullet_bank: List[dict] = []
    answer_library: dict = {}
    proof_pack: List[dict] = []
    apply_policy: ApplyPolicy


class WorkflowStatus(BaseModel):
    user_id: str
    status: str
    applications_submitted: int
    applications_failed: int
    current_job_index: int
    total_jobs: int
    logs: List[str]


@router.post("/start")
async def start_workflow(request: StartWorkflowRequest, background_tasks: BackgroundTasks):
    """
    Start the autonomous job application workflow.
    Runs in background and can be monitored via /status endpoint.
    """
    user_id = request.user_id
    
    if user_id in active_workflows and active_workflows[user_id].get("status") == "running":
        raise HTTPException(status_code=400, detail="Workflow already running for this user")
    
    # Initialize workflow state
    initial_state: AgentState = {
        "user_id": user_id,
        "student_profile": request.student_profile,
        "bullet_bank": request.bullet_bank,
        "answer_library": request.answer_library,
        "proof_pack": request.proof_pack,
        "apply_policy": request.apply_policy.model_dump(),
        "job_queue": [],
        "applied_job_ids": tracker.get_applied_job_ids(user_id),
        "current_job_index": 0,
        "current_job": {},
        "match_score": 0.0,
        "match_reasoning": "",
        "tailored_resume": {},
        "tailored_cover_letter": "",
        "evidence_mapping": [],
        "applications_submitted": [],
        "kill_switch": False,
        "errors": [],
        "logs": [],
        "should_continue": True
    }
    
    # Track workflow status
    active_workflows[user_id] = {
        "status": "running",
        "state": initial_state,
        "kill_switch": False
    }
    
    # Run workflow in background
    background_tasks.add_task(run_workflow_async, user_id, initial_state)
    
    return {
        "success": True,
        "message": "Workflow started",
        "user_id": user_id
    }


async def run_workflow_async(user_id: str, initial_state: AgentState):
    """Run the workflow asynchronously"""
    try:
        # Run the compiled workflow
        final_state = await app_workflow.ainvoke(initial_state)
        
        active_workflows[user_id]["status"] = "completed"
        active_workflows[user_id]["state"] = final_state
        
    except Exception as e:
        active_workflows[user_id]["status"] = "failed"
        active_workflows[user_id]["error"] = str(e)


@router.get("/status/{user_id}")
async def get_workflow_status(user_id: str):
    """Get current status of user's workflow"""
    if user_id not in active_workflows:
        raise HTTPException(status_code=404, detail="No workflow found for this user")
    
    workflow = active_workflows[user_id]
    state = workflow.get("state", {})
    
    applications = state.get("applications_submitted", [])
    submitted = len([a for a in applications if a.get("status") == "submitted"])
    failed = len([a for a in applications if a.get("status") == "failed"])
    
    return {
        "user_id": user_id,
        "status": workflow.get("status"),
        "applications_submitted": submitted,
        "applications_failed": failed,
        "current_job_index": state.get("current_job_index", 0),
        "total_jobs": len(state.get("job_queue", [])),
        "logs": state.get("logs", [])[-20:],  # Last 20 logs
        "errors": state.get("errors", [])
    }


@router.post("/kill/{user_id}")
async def kill_workflow(user_id: str):
    """
    Activate kill switch to stop the workflow.
    The workflow will stop after completing the current application.
    """
    if user_id not in active_workflows:
        raise HTTPException(status_code=404, detail="No workflow found for this user")
    
    active_workflows[user_id]["kill_switch"] = True
    
    # Update the state if workflow is still running
    if active_workflows[user_id].get("status") == "running":
        active_workflows[user_id]["state"]["kill_switch"] = True
    
    return {
        "success": True,
        "message": "Kill switch activated. Workflow will stop after current application."
    }


@router.get("/results/{user_id}")
async def get_workflow_results(user_id: str):
    """Get final results of completed workflow"""
    if user_id not in active_workflows:
        raise HTTPException(status_code=404, detail="No workflow found")
    
    workflow = active_workflows[user_id]
    state = workflow.get("state", {})
    
    return {
        "user_id": user_id,
        "status": workflow.get("status"),
        "job_queue": state.get("job_queue", []),
        "applications": state.get("applications_submitted", []),
        "logs": state.get("logs", []),
        "errors": state.get("errors", [])
    }
