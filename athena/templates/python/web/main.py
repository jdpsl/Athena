"""
{{project_name}} - {{description}}
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from {{project_name_snake}}.config import settings

app = FastAPI(
    title="{{project_name}}",
    description="{{description}}",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "{{project_name}} API is running",
        "version": "0.1.0"
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": settings.environment
    }


# Include routers here
# Example:
# from {{project_name_snake}}.routers import items
# app.include_router(items.router, prefix="/items", tags=["items"])
