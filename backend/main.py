from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import auth, resume, workflow, tracker, websocket

app = FastAPI(
    title="Job Application Agent API",
    description="Autonomous job search and application agent",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(resume.router)
app.include_router(workflow.router)
app.include_router(tracker.router)
app.include_router(websocket.router)


@app.get("/")
def health_check():
    """Health check endpoint"""
    return {
        "status": "online",
        "sandbox_url": settings.SANDBOX_API_URL,
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
