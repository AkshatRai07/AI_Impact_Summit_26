from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.db.tracker import ApplicationTracker

router = APIRouter(prefix="/tracker", tags=["Application Tracker"])
tracker = ApplicationTracker()


@router.get("/applications/{user_id}")
async def get_applications(
    user_id: str,
    status: Optional[str] = Query(None, description="Filter by status: queued, submitted, failed, retried")
):
    """
    Get all applications for a user with optional status filter.
    Returns application tracker with receipts and confirmation IDs.
    """
    try:
        applications = tracker.get_user_applications(user_id)
        
        if status:
            applications = [a for a in applications if a.get("status") == status]
        
        # Calculate summary stats
        total = len(applications)
        submitted = len([a for a in applications if a.get("status") == "submitted"])
        failed = len([a for a in applications if a.get("status") == "failed"])
        
        return {
            "user_id": user_id,
            "summary": {
                "total": total,
                "submitted": submitted,
                "failed": failed,
                "success_rate": round(submitted / total * 100, 1) if total > 0 else 0
            },
            "applications": applications
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/applications/{user_id}/{job_id}")
async def get_application_detail(user_id: str, job_id: str):
    """Get detailed info for a specific application including evidence mapping"""
    try:
        applications = tracker.get_user_applications(user_id)
        for app in applications:
            if app.get("job_id") == job_id:
                return app
        raise HTTPException(status_code=404, detail="Application not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/applications/{user_id}/{job_id}/retry")
async def retry_application(user_id: str, job_id: str):
    """Mark a failed application for retry"""
    try:
        applications = tracker.get_user_applications(user_id)
        for app in applications:
            if app.get("job_id") == job_id and app.get("status") == "failed":
                app["status"] = "queued"
                app["retry_count"] = app.get("retry_count", 0) + 1
                tracker.update_application(user_id, job_id, app)
                return {"success": True, "message": "Application queued for retry"}
        
        raise HTTPException(status_code=404, detail="Failed application not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/applications/{user_id}")
async def clear_applications(user_id: str):
    """Clear all applications for a user (for testing)"""
    from app.tools.sandbox_api import SandboxAPIClient
    sandbox_client = SandboxAPIClient()
    
    try:
        # Clear from local tracker
        tracker.clear_user_applications(user_id)
        
        # Also clear from sandbox
        try:
            await sandbox_client.clear_applications()
        except Exception as e:
            print(f"Warning: Could not clear sandbox applications: {e}")
        
        return {"success": True, "message": "Applications cleared from tracker and sandbox"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
