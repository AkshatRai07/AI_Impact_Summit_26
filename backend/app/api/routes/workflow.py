from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import json

from app.graph.workflow import app_workflow
from app.graph.state import AgentState
from app.db.tracker import ApplicationTracker

router = APIRouter(prefix="/workflow", tags=["Workflow"])
tracker = ApplicationTracker()

# Store for active workflows (for kill switch)
active_workflows: dict = {}

# SSE event queues per user
sse_queues: Dict[str, asyncio.Queue] = {}


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


async def send_sse_event(user_id: str, event_type: str, data: dict):
    """Send an SSE event to the user's queue"""
    if user_id in sse_queues:
        event = {"type": event_type, **data}
        await sse_queues[user_id].put(event)
        print(f"[SSE] Sent {event_type} to {user_id}")


async def sse_event_generator(user_id: str):
    """Generator that yields SSE events for a user"""
    # Create queue for this user
    sse_queues[user_id] = asyncio.Queue()
    queue = sse_queues[user_id]
    
    try:
        while True:
            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield f"data: {json.dumps(event)}\n\n"
                
                # Stop streaming if workflow ended
                if event.get("type") in ["workflow_completed", "workflow_failed"]:
                    break
            except asyncio.TimeoutError:
                # Send keepalive
                yield f": keepalive\n\n"
    finally:
        # Cleanup queue
        sse_queues.pop(user_id, None)


@router.get("/stream/{user_id}")
async def stream_workflow_events(user_id: str):
    """SSE endpoint for real-time workflow updates"""
    return StreamingResponse(
        sse_event_generator(user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )


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
    """Run the workflow asynchronously with SSE streaming"""
    try:
        print(f"[WORKFLOW] Starting workflow for user {user_id}")
        
        # Send workflow started event
        await send_sse_event(user_id, "workflow_started", {
            "message": "Workflow started"
        })
        
        # Run the workflow with streaming to catch each node output
        # Increase recursion limit to handle many jobs (each job = 4+ nodes)
        config = {"recursion_limit": 200}
        async for event in app_workflow.astream(initial_state, stream_mode="updates", config=config):
            for node_name, node_output in event.items():
                print(f"[WORKFLOW] Node {node_name} completed")
                
                # Update active workflow state
                if node_output:
                    current_state = active_workflows[user_id].get("state", {})
                    current_state.update(node_output)
                    active_workflows[user_id]["state"] = current_state
                
                # Get current state for tracking
                state = active_workflows[user_id].get("state", {})
                job_queue = state.get("job_queue", [])
                current_idx = state.get("current_job_index", 0)
                total_jobs = len(job_queue)
                
                # Send appropriate SSE event based on node
                if node_name == "fetch_jobs":
                    await send_sse_event(user_id, "jobs_fetched", {
                        "total_jobs": len(node_output.get("job_queue", [])),
                        "jobs": node_output.get("job_queue", [])[:5]
                    })
                    
                elif node_name == "personalize":
                    current_job = node_output.get("current_job", {})
                    await send_sse_event(user_id, "job_processing", {
                        "job": current_job,
                        "current_index": current_idx,
                        "total_jobs": total_jobs,
                        "tailored_resume": node_output.get("tailored_resume", {}),
                        "tailored_cover_letter": node_output.get("tailored_cover_letter", "")
                    })
                    
                elif node_name == "apply":
                    applications = node_output.get("applications_submitted", [])
                    new_idx = node_output.get("current_job_index", current_idx)
                    if applications:
                        latest = applications[-1]
                        # Get all apps including new ones from this update
                        all_apps = state.get("applications_submitted", [])
                        # Count from all apps (state already updated above)
                        submitted_count = len([a for a in all_apps if a.get("status") == "submitted"])
                        failed_count = len([a for a in all_apps if a.get("status") == "failed"])
                        
                        await send_sse_event(user_id, "application_result", {
                            "application": {
                                "job_id": latest.get("job_id"),
                                "job_title": latest.get("job_title"),
                                "company": latest.get("company"),
                                "status": latest.get("status"),
                                "confirmation_id": latest.get("confirmation_id"),
                                "error_message": latest.get("error_message"),
                                "cover_letter": latest.get("cover_letter"),
                            },
                            "status": latest.get("status", "unknown"),
                            "current_index": new_idx,
                            "total_jobs": total_jobs,
                            "total_submitted": submitted_count,
                            "total_failed": failed_count
                        })
                        
                elif node_name == "skip_job":
                    new_idx = node_output.get("current_job_index", current_idx)
                    await send_sse_event(user_id, "job_skipped", {
                        "current_index": new_idx,
                        "total_jobs": total_jobs,
                        "reason": "Low match score or safety check failed"
                    })
        
        # Workflow completed
        final_state = active_workflows[user_id].get("state", {})
        active_workflows[user_id]["status"] = "completed"
        
        applications = final_state.get("applications_submitted", [])
        await send_sse_event(user_id, "workflow_completed", {
            "total_submitted": len([a for a in applications if a.get("status") == "submitted"]),
            "total_failed": len([a for a in applications if a.get("status") == "failed"]),
            "message": "Workflow completed successfully"
        })
        
        print(f"[WORKFLOW] Completed for user {user_id}")
        print(f"[WORKFLOW] Jobs processed: {len(applications)}")
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"[WORKFLOW ERROR] {error_msg}")
        print(f"[WORKFLOW TRACEBACK] {error_trace}")
        
        active_workflows[user_id]["status"] = "failed"
        active_workflows[user_id]["error"] = error_msg
        
        # Update state with error
        current_state = active_workflows[user_id].get("state", initial_state)
        current_state["errors"] = current_state.get("errors", []) + [error_msg]
        current_state["logs"] = current_state.get("logs", []) + [f"❌ Workflow failed: {error_msg}"]
        active_workflows[user_id]["state"] = current_state
        
        # Send failure event
        await send_sse_event(user_id, "workflow_failed", {
            "error": error_msg,
            "message": "Workflow failed"
        })


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
