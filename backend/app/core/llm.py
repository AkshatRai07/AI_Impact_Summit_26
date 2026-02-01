from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

def get_llm(temperature: float = 0.0):
    """
    Returns a configured Gemini instance.
    """
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=temperature,
        convert_system_message_to_human=True
    )

llm = get_llm()
