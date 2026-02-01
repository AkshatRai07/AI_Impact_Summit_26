import json
import re
import io
from pypdf import PdfReader
from app.core.llm import llm
from langchain_core.messages import HumanMessage, SystemMessage


def extract_text_from_pdf(file_input) -> str:
    """Extract text content from a PDF file. Accepts file path (str) or bytes."""
    if isinstance(file_input, str):
        reader = PdfReader(file_input)
    elif isinstance(file_input, bytes):
        reader = PdfReader(io.BytesIO(file_input))
    else:
        reader = PdfReader(file_input)
    
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


async def parse_resume_to_profile(resume_text: str, additional_info: dict = None) -> dict:
    """
    Parse resume text into a structured student profile with all required artifacts.
    Uses LLM to extract and structure information - NEVER invents data.
    """
    
    additional_context = ""
    if additional_info:
        if additional_info.get("linkedin_text"):
            additional_context += f"\n\nLinkedIn Profile:\n{additional_info['linkedin_text']}"
        if additional_info.get("github_url"):
            additional_context += f"\n\nGitHub: {additional_info['github_url']}"
        if additional_info.get("portfolio_url"):
            additional_context += f"\n\nPortfolio: {additional_info['portfolio_url']}"
        if additional_info.get("additional_projects"):
            additional_context += f"\n\nAdditional Projects:\n{additional_info['additional_projects']}"
    
    system_prompt = """You are a resume parser that extracts ONLY factual information. 
CRITICAL RULES:
1. NEVER invent, embellish, or assume any information
2. Extract ONLY what is explicitly stated in the resume
3. If information is not present, use null or empty arrays
4. All bullets must be direct quotes or close paraphrases from the resume
5. All proof links must be explicitly mentioned in the resume

You must return a valid JSON object with this EXACT structure:
{
    "student_profile": {
        "name": "string or null",
        "email": "string or null",
        "phone": "string or null",
        "location": "string or null",
        "linkedin_url": "string or null",
        "github_url": "string or null",
        "portfolio_url": "string or null",
        "summary": "string - brief factual summary or null",
        "education": [
            {
                "institution": "string",
                "degree": "string",
                "field": "string or null",
                "graduation_date": "string or null",
                "gpa": "string or null",
                "coursework": ["string"],
                "achievements": ["string"]
            }
        ],
        "experience": [
            {
                "company": "string",
                "title": "string",
                "location": "string or null",
                "start_date": "string or null",
                "end_date": "string or null",
                "description": "string",
                "bullets": ["string - exact achievement bullets from resume"],
                "technologies": ["string"]
            }
        ],
        "projects": [
            {
                "name": "string",
                "description": "string",
                "technologies": ["string"],
                "url": "string or null",
                "bullets": ["string - exact achievement bullets"],
                "date": "string or null"
            }
        ],
        "skills": {
            "languages": ["string"],
            "frameworks": ["string"],
            "tools": ["string"],
            "other": ["string"]
        },
        "certifications": ["string"],
        "awards": ["string"],
        "constraints": {
            "preferred_locations": ["string"],
            "open_to_remote": true,
            "requires_visa_sponsorship": null,
            "earliest_start_date": null,
            "salary_expectations": null
        }
    },
    "bullet_bank": [
        {
            "id": "bullet_1",
            "text": "exact achievement bullet from resume",
            "source": "experience|project|education",
            "source_name": "company or project name",
            "skills_demonstrated": ["string"],
            "metrics": "any numbers/metrics mentioned or null",
            "category": "technical|leadership|impact|teamwork|other"
        }
    ],
    "answer_library": {
        "work_authorization": "Extract if mentioned, otherwise null",
        "visa_sponsorship_needed": null,
        "earliest_start_date": null,
        "relocation_willingness": null,
        "salary_expectations": null,
        "why_interested_template": "Based on their background, a factual template or null",
        "greatest_strength": "Based on evidence in resume or null",
        "availability": null
    },
    "proof_pack": [
        {
            "type": "github|portfolio|demo|publication|certificate|other",
            "url": "string",
            "title": "string",
            "description": "what it demonstrates",
            "related_skills": ["string"]
        }
    ]
}

Extract ALL information from the resume. For bullet_bank, include EVERY achievement bullet from experience and projects sections."""

    user_prompt = f"""Parse this resume and extract all information into the required JSON structure.

RESUME TEXT:
{resume_text}
{additional_context}

Remember: Extract ONLY what is explicitly stated. Never invent information.
Return ONLY the JSON object, no other text."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    response = await llm.ainvoke(messages)
    content = response.content.strip()
    
    # Extract JSON from response
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        # Try to find JSON object in response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
        else:
            raise ValueError("Failed to parse LLM response as JSON")
    
    # Ensure all required keys exist
    if "student_profile" not in parsed:
        parsed = {"student_profile": parsed, "bullet_bank": [], "answer_library": {}, "proof_pack": []}
    
    if "bullet_bank" not in parsed:
        parsed["bullet_bank"] = []
    if "answer_library" not in parsed:
        parsed["answer_library"] = {}
    if "proof_pack" not in parsed:
        parsed["proof_pack"] = []
    
    return parsed
