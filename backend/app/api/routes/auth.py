# filepath: backend/app/api/routes/auth.py
"""
Simple auth system - stores users in Supabase database (not Supabase Auth)
Uses SHA-256 for password hashing and JWT for tokens
"""
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from app.db.supabase import supabase
from app.schemas.auth import UserAuth, UserResponse
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

# In-memory fallback for users if Supabase is not configured
_memory_users: dict = {}


def hash_password(password: str) -> str:
    """Simple password hashing using SHA-256 with salt"""
    salt = "hackathon_salt_2026"
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed


def create_token(user_id: str, email: str) -> str:
    """Create a simple JWT token"""
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(days=7),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


@router.post("/signup", response_model=UserResponse)
async def register(user_data: UserAuth):
    """Register a new user - stores in database, returns token immediately"""
    email = user_data.email.lower().strip()
    password_hash = hash_password(user_data.password)
    
    # Try Supabase database first
    if supabase:
        try:
            # Check if user already exists
            existing = supabase.table("users").select("id").eq("email", email).execute()
            if existing.data and len(existing.data) > 0:
                raise HTTPException(status_code=400, detail="Email already registered")
            
            # Create new user
            user_id = secrets.token_hex(16)
            result = supabase.table("users").insert({
                "id": user_id,
                "email": email,
                "password_hash": password_hash,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            
            if not result.data:
                raise HTTPException(status_code=400, detail="Failed to create user")
            
            token = create_token(user_id, email)
            return UserResponse(id=user_id, email=email, access_token=token)
            
        except HTTPException:
            raise
        except Exception as e:
            # If table doesn't exist or other DB error, fall back to memory
            print(f"Supabase error (using memory): {e}")
    
    # Fallback to in-memory storage
    if email in _memory_users:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = secrets.token_hex(16)
    _memory_users[email] = {
        "id": user_id,
        "email": email,
        "password_hash": password_hash
    }
    
    token = create_token(user_id, email)
    return UserResponse(id=user_id, email=email, access_token=token)


@router.post("/login", response_model=UserResponse)
async def login(user_data: UserAuth):
    """Login user - verify password and return token"""
    email = user_data.email.lower().strip()
    password_hash = hash_password(user_data.password)
    
    # Try Supabase database first
    if supabase:
        try:
            result = supabase.table("users").select("*").eq("email", email).execute()
            
            if result.data and len(result.data) > 0:
                user = result.data[0]
                if user.get("password_hash") == password_hash:
                    token = create_token(user["id"], email)
                    return UserResponse(id=user["id"], email=email, access_token=token)
                else:
                    raise HTTPException(status_code=401, detail="Invalid password")
            else:
                raise HTTPException(status_code=401, detail="User not found")
                
        except HTTPException:
            raise
        except Exception as e:
            # Fall back to memory
            print(f"Supabase error (using memory): {e}")
    
    # Fallback to in-memory storage
    if email not in _memory_users:
        raise HTTPException(status_code=401, detail="User not found")
    
    user = _memory_users[email]
    if user["password_hash"] != password_hash:
        raise HTTPException(status_code=401, detail="Invalid password")
    
    token = create_token(user["id"], email)
    return UserResponse(id=user["id"], email=email, access_token=token)
