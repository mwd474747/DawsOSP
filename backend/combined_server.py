import os
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

# Imports for Replit compatibility
try:
    from replit import db, env
except ImportError:
    db = None
    env = None

# Imports for the application
from app.config import Config
from app.core.auth import AuthManager
from app.core.logging import Logger
from app.core.rate_limiter import RateLimiter
from app.core.provider_registry import ProviderRegistry
from app.integrations.provider_registry import get_provider_registry
from app.integrations.shared.errors import APIError
from app.integrations.shared.utils import process_api_error
from app.models.user import User
from app.routers import (
    auth,
    chatbot,
    dashboard,
    data_sources,
    executor,
    feedback,
    files,
    integrations,
    monitor,
    profile,
    settings,
    sources,
    user,
)
from app.services.data_harvester import DataHarvester
from app.services.event_stream import EventStreamService
from app.services.user_service import UserService
from app.services.workflow_service import WorkflowService

# Setup for Replit DB if available
if db:
    print("Replit DB enabled.")
    # Placeholder for any DB-specific setup if needed later
else:
    print("Replit DB not available.")

# Instantiate services and managers
config = Config()
auth_manager = AuthManager(config.JWT_SECRET_KEY)
rate_limiter = RateLimiter(max_requests=config.RATE_LIMIT_MAX, period=config.RATE_LIMIT_PERIOD)
logger = Logger(__name__)
user_service = UserService(db=db)  # Pass db here if it's available
event_stream_service = EventStreamService()
workflow_service = WorkflowService(user_service=user_service)


# Initialize FastAPI app
app = FastAPI(
    title="DawsOS API",
    description="API for DawsOS - Your AI-powered Operating System",
    version="0.1.0",
)

# Mount static files for frontend
# Use Path(__file__).resolve().parent to get the directory of the current file
# then navigate to the 'frontend/dist' directory
frontend_dist_path = Path(__file__).resolve().parent / "frontend" / "dist"
if frontend_dist_path.exists():
    app.mount(
        "/", StaticFiles(directory=frontend_dist_path, html=True), name="static-frontend"
    )
    print(f"Serving frontend from: {frontend_dist_path}")
else:
    print(f"Frontend dist not found at: {frontend_dist_path}. Serving API only.")


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(user.router, prefix="/api/user", tags=["User"])
app.include_router(chatbot.router, prefix="/api/chatbot", tags=["Chatbot"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(data_sources.router, prefix="/api/data_sources", tags=["Data Sources"])
app.include_router(executor.router, prefix="/api/executor", tags=["Executor"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback"])
app.include_router(files.router, prefix="/api/files", tags=["Files"])
app.include_router(integrations.router, prefix="/api/integrations", tags=["Integrations"])
app.include_router(monitor.router, prefix="/api/monitor", tags=["Monitor"])
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
app.include_router(sources.router, prefix="/api/sources", tags=["Sources"])


# Middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=config.SESSION_SECRET_KEY,
    max_age=3600,  # 1 hour
)


# --- API Endpoints ---


@app.get("/api/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "message": "DawsOS API is running!"}


@app.post("/api/execute_workflow")
async def execute_workflow_endpoint(request: Request):
    """
    Executes a given workflow.
    Expects a JSON payload with a 'workflow_id' and 'user_id'.
    """
    try:
        data = await request.json()
        workflow_id = data.get("workflow_id")
        user_id = data.get("user_id")

        if not workflow_id or not user_id:
            raise HTTPException(
                status_code=400, detail="Missing 'workflow_id' or 'user_id'."
            )

        # Simulate workflow execution
        result = await workflow_service.execute_workflow(workflow_id, user_id)
        return {"status": "success", "result": result}

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.post("/api/trigger_data_harvesting")
async def trigger_data_harvesting_endpoint(request: Request):
    """
    Triggers the data harvesting process for specified integrations.
    Expects a JSON payload with 'user_id' and a list of 'integrations'.
    """
    try:
        data = await request.json()
        user_id = data.get("user_id")
        integrations_to_harvest = data.get("integrations")

        if not user_id or not integrations_to_harvest:
            raise HTTPException(
                status_code=400, detail="Missing 'user_id' or 'integrations' list."
            )

        # Instantiate DataHarvester here or inject it if it's a singleton
        # For simplicity, instantiating here. Consider dependency injection for complex apps.
        data_harvester = DataHarvester(user_id=user_id)

        # Use BackgroundTasks to run harvesting without blocking the response
        # This is crucial for long-running operations
        background_tasks = BackgroundTasks()
        background_tasks.add_task(
            data_harvester.harvest_all, integrations_to_harvest
        )

        return {
            "message": "Data harvesting triggered successfully in the background.",
            "user_id": user_id,
            "integrations": integrations_to_harvest,
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error triggering data harvesting: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# --- Error Handling ---


@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    """Handles custom APIError exceptions."""
    logger.error(f"API Error: {exc.message} (Status Code: {exc.status_code})")
    return process_api_error(exc)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handles FastAPI's HTTPException."""
    logger.error(f"HTTP Exception: {exc.detail} (Status Code: {exc.status_code})")
    return process_api_error(APIError(message=exc.detail, status_code=exc.status_code))


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handles any other unhandled exceptions."""
    logger.exception(f"Unhandled Exception: {exc}")  # Use logger.exception to log traceback
    return process_api_error(
        APIError(
            message="An unexpected error occurred. Please try again later.",
            status_code=500,
        )
    )


# --- Routes for Serving Frontend (if not handled by StaticFiles) ---
# This is a fallback or alternative if StaticFiles isn't used or for specific routes

@app.get("/")
async def read_root():
    """Serves the main index.html for the frontend."""
    # This route is typically handled by StaticFiles if the directory is mounted at "/"
    # If StaticFiles is mounted at a different path or not at all, this would be needed.
    # Assuming StaticFiles is mounted at "/", this might be redundant.
    return FileResponse(frontend_dist_path / "index.html")


@app.get("/{path:path}")
async def serve_frontend_files(path: str):
    """Serves other frontend static files."""
    # Again, usually handled by StaticFiles. This is a fallback.
    file_path = frontend_dist_path / path
    if file_path.is_file():
        return FileResponse(file_path)
    else:
        # If a requested path doesn't exist as a file, return index.html
        # to allow client-side routing to handle it.
        return FileResponse(frontend_dist_path / "index.html")


# --- Main Execution Block ---

if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.environ.get("PORT", 5000))

    print("=" * 80)
    print(f"Starting DawsOS Combined Server on port {port}")
    print("=" * 80)

    # Validate API keys on startup
    from app.integrations.provider_registry import get_provider_registry

    print("\n🔍 Validating API Keys...")
    registry = get_provider_registry()
    validation = registry.validate_all_keys()

    for key, present in validation.items():
        status = "✅" if present else "⚠️ "
        print(f"  {status} {key}: {'Configured' if present else 'Missing (will use stubs)'}")

    print("")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )