from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.api.deps import manager

router = APIRouter()

@router.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, receive any client messages
            data = await websocket.receive_text()
            # Echo or handle commands if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)
