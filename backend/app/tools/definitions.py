from langchain_core.tools import tool
from app.tools.sandbox_api import SandboxAPIClient  # Fixed import
from typing import List

# Initialize the client
sandbox_client = SandboxAPIClient()

@tool
async def fetch_job_listings(query: str = "all") -> str:
    """
    Fetches the current list of available job openings from the sandbox job portal.
    Use this to see what jobs are available to apply for.
    """
    try:
        jobs = await sandbox_client.fetch_jobs()
        # Return a simplified string for the LLM to digest
        return "\n".join([f"ID: {j.get('id')} | Title: {j.get('title')} | Desc: {j.get('description')}" for j in jobs])
    except Exception as e:
        return f"Error fetching jobs: {str(e)}"

@tool
async def submit_application_tool(job_id: str, tailored_resume: str, cover_letter: str) -> str:
    """
    Submits a final application to the job portal.
    REQUIRES: A tailored resume text and a cover letter.
    """
    payload = {
        "job_id": job_id,
        "applicant_name": "Student",
        "applicant_email": "student@example.com",
        "resume": tailored_resume,
        "cover_letter": cover_letter
    }
    try:
        res = await sandbox_client.submit_application(payload)
        return f"Application Submitted Successfully: {res}"
    except Exception as e:
        return f"Submission Failed: {str(e)}"

# List of tools for binding
ALL_TOOLS = [fetch_job_listings, submit_application_tool]
