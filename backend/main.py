import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from .config import config
from .models.database import init_db
from .api.routes import router
from .scheduler import start_scheduler, stop_scheduler

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent Networking Tool",
    description="AI-powered networking assistant with multiple specialized agents",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Serve frontend static files
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
print(f"Frontend path: {frontend_path}")
print(f"Frontend exists: {os.path.exists(frontend_path)}")

@app.get("/")
async def serve_frontend():
    """Serve the frontend index.html"""
    index_path = os.path.join(frontend_path, "index.html")
    print(f"Serving index from: {index_path}")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend not found", "path": frontend_path, "index_exists": os.path.exists(index_path)}

# Mount static files for JS and CSS
if os.path.exists(frontend_path):
    try:
        app.mount("/static", StaticFiles(directory=frontend_path), name="static")
        print("✅ Static files mounted")
    except Exception as e:
        print(f"❌ Failed to mount static files: {e}")


@app.on_event("startup")
async def startup_event():
    """Initialize database and validate config on startup"""
    print("🚀 Starting Multi-Agent Networking Tool...")

    try:
        # Validate configuration
        config.validate()
        print("✅ Configuration validated")

        # Initialize database
        init_db(config.DATABASE_URL)
        print(f"✅ Database initialized at {config.DATABASE_URL}")

        # Start scheduler
        start_scheduler()

        print(f"🌐 Server starting on {config.HOST}:{config.PORT}")
        print("📝 API docs available at http://localhost:8000/docs")

    except Exception as e:
        print(f"❌ Startup failed: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Shutting down Multi-Agent Networking Tool...")
    stop_scheduler()


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
