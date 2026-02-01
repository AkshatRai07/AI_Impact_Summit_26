# filepath: backend/app/api/routes/auth.py
from fastapi import APIRouter, HTTPException
from app.db.supabase import supabase
from app.schemas.auth import UserAuth, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=UserResponse)
async def register(user_data: UserAuth):
    if not supabase:
        raise HTTPException(status_code=503, detail="Authentication service not configured")
    
    try:
        res = supabase.auth.sign_up({
            "email": user_data.email, 
            "password": user_data.password
        })
        
        if not res.user:
            raise HTTPException(status_code=400, detail="Signup failed")
            
        return UserResponse(
            id=res.user.id,
            email=res.user.email,
            access_token=res.session.access_token,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=UserResponse)
async def login(user_data: UserAuth):
    if not supabase:
        raise HTTPException(status_code=503, detail="Authentication service not configured")
    
    try:
        res = supabase.auth.sign_in_with_password({
            "email": user_data.email, 
            "password": user_data.password
        })
        
        if not res.session:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        return UserResponse(
            id=res.user.id,
            email=res.user.email,
            access_token=res.session.access_token,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
