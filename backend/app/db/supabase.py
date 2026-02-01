from supabase import create_client, Client
from app.core.config import settings
from typing import Optional

supabase: Optional[Client] = None

if settings.SUPABASE_URL and settings.SUPABASE_KEY:
    try:
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    except Exception as e:
        print(f"Warning: Could not connect to Supabase: {e}")
        supabase = None
else:
    print("Warning: Supabase credentials not configured, using in-memory storage")
