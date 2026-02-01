from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    
    # Supabase
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None  # ADD THIS - used by supabase.py
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # Google AI (Gemini) - ADD THIS
    GOOGLE_API_KEY: Optional[str] = None
    
    # JWT Secret for simple auth
    JWT_SECRET: str = "hackathon-secret-key-change-in-production"
    
    # Sandbox - Go server at localhost:8080
    SANDBOX_API_URL: str = "http://localhost:8080"
    SANDBOX_URL: str = "http://localhost:8080"
    
    # LangGraph
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
