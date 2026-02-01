from typing import Optional
from datetime import datetime
from app.db.supabase import supabase


class ApplicationTracker:
    """
    Tracks all job applications with status, confirmations, and history.
    Uses Supabase for persistence, falls back to in-memory for demo.
    """
    
    def __init__(self):
        self._memory_store: dict = {}  # Fallback in-memory storage
    
    def add_application(self, user_id: str, application: dict) -> None:
        """Add or update an application record"""
        application["updated_at"] = datetime.utcnow().isoformat()
        
        if supabase:
            try:
                supabase.table("applications").upsert({
                    "user_id": user_id,
                    "job_id": application.get("job_id"),
                    "job_title": application.get("job_title"),
                    "company": application.get("company"),
                    "status": application.get("status"),
                    "confirmation_id": application.get("confirmation_id"),
                    "submitted_at": application.get("submitted_at"),
                    "error_message": application.get("error_message"),
                    "retry_count": application.get("retry_count", 0),
                    "tailored_resume": application.get("tailored_resume"),
                    "cover_letter": application.get("cover_letter"),
                    "evidence_mapping": application.get("evidence_mapping"),
                    "updated_at": application["updated_at"]
                }).execute()
                return
            except Exception as e:
                print(f"Supabase error, using memory: {e}")
        
        # Fallback to memory
        if user_id not in self._memory_store:
            self._memory_store[user_id] = []
        
        # Update existing or add new
        job_id = application.get("job_id")
        for i, app in enumerate(self._memory_store[user_id]):
            if app.get("job_id") == job_id:
                self._memory_store[user_id][i] = application
                return
        
        self._memory_store[user_id].append(application)
    
    def get_user_applications(self, user_id: str) -> list:
        """Get all applications for a user"""
        if supabase:
            try:
                result = supabase.table("applications").select("*").eq("user_id", user_id).order("updated_at", desc=True).execute()
                return result.data or []
            except Exception as e:
                print(f"Supabase error, using memory: {e}")
        
        return self._memory_store.get(user_id, [])
    
    def get_applied_job_ids(self, user_id: str) -> list:
        """Get list of job IDs already applied to"""
        applications = self.get_user_applications(user_id)
        return [app.get("job_id") for app in applications if app.get("job_id")]
    
    def update_application(self, user_id: str, job_id: str, updates: dict) -> bool:
        """Update an existing application"""
        updates["updated_at"] = datetime.utcnow().isoformat()
        
        if supabase:
            try:
                supabase.table("applications").update(updates).eq("user_id", user_id).eq("job_id", job_id).execute()
                return True
            except Exception as e:
                print(f"Supabase error: {e}")
        
        # Memory fallback
        if user_id in self._memory_store:
            for i, app in enumerate(self._memory_store[user_id]):
                if app.get("job_id") == job_id:
                    self._memory_store[user_id][i].update(updates)
                    return True
        return False
    
    def clear_user_applications(self, user_id: str) -> None:
        """Clear all applications for a user"""
        if supabase:
            try:
                supabase.table("applications").delete().eq("user_id", user_id).execute()
            except:
                pass
        
        self._memory_store.pop(user_id, None)
