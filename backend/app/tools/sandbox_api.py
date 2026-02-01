import httpx
from app.core.config import settings


class SandboxAPIClient:
    """Client for interacting with the Go sandbox job portal at localhost:8080"""
    
    def __init__(self):
        self.base_url = settings.SANDBOX_API_URL.rstrip("/")
        self.timeout = 30.0
    
    async def fetch_jobs(self, limit: int = 100) -> list:
        """Fetch available jobs from the sandbox portal"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(f"{self.base_url}/api/jobs", params={"limit": limit})
                response.raise_for_status()
                data = response.json()
                
                # Handle different response formats
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return data.get("jobs", data.get("data", []))
                return []
                
            except httpx.HTTPStatusError as e:
                raise Exception(f"Sandbox API error: {e.response.status_code} - {e.response.text}")
            except httpx.RequestError as e:
                raise Exception(f"Sandbox connection error: {str(e)}")
    
    async def get_job_details(self, job_id: str) -> dict:
        """Get detailed information about a specific job"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(f"{self.base_url}/api/jobs/{job_id}")
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise Exception(f"Failed to get job {job_id}: {e.response.status_code}")
            except httpx.RequestError as e:
                raise Exception(f"Connection error: {str(e)}")
    
    async def submit_application(self, payload: dict) -> dict:
        """
        Submit a job application to the sandbox.
        
        Expected payload:
        {
            "job_id": str,
            "applicant_name": str,
            "applicant_email": str,
            "resume": str,
            "cover_letter": str
        }
        
        Returns confirmation with application_id/confirmation_id
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # Try the standard endpoint first
                response = await client.post(
                    f"{self.base_url}/api/applications",
                    json=payload
                )
                
                # Handle rate limiting
                if response.status_code == 429:
                    raise Exception("Rate limited - too many requests")
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                error_detail = e.response.text if e.response else str(e)
                raise Exception(f"Application submission failed: {e.response.status_code} - {error_detail}")
            except httpx.RequestError as e:
                raise Exception(f"Connection error during submission: {str(e)}")
    
    async def get_application_status(self, application_id: str) -> dict:
        """Check status of a submitted application"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(f"{self.base_url}/api/applications/{application_id}")
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise Exception(f"Failed to get application status: {e.response.status_code}")
            except httpx.RequestError as e:
                raise Exception(f"Connection error: {str(e)}")
    
    async def health_check(self) -> bool:
        """Check if sandbox is running"""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
            except:
                return False
    
    async def clear_applications(self) -> dict:
        """Clear all applications in sandbox (for testing)"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.delete(f"{self.base_url}/api/applications/clear")
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise Exception(f"Failed to clear applications: {e.response.status_code}")
            except httpx.RequestError as e:
                raise Exception(f"Connection error: {str(e)}")
