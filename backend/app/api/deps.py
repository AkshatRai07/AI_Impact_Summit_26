# filepath: backend/app/api/deps.py
import json
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.db.supabase import supabase
from app.core.config import settings
from typing import List, Optional
from fastapi import WebSocket


class ConnectionManager:
    """WebSocket connection manager for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message):
        """Broadcast message to all connected clients. Accepts str or dict."""
        if isinstance(message, dict):
            message = json.dumps(message)
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        
        # Clean up disconnected
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()

# Defines that we expect a "Bearer <token>" header
security = HTTPBearer(auto_error=False)  # Don't auto-error for optional auth


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Get current user from JWT token"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    token = credentials.credentials
    try:
        # Decode our custom JWT token
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if not user_id or not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Return a simple user object
        return {"id": user_id, "email": email}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Optional authentication - returns None if not authenticated"""
    if not credentials:
        return None
    
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        email = payload.get("email")
        if user_id and email:
            return {"id": user_id, "email": email}
        return None
    except:
        return None
