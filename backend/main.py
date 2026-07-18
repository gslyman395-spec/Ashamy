"""
Application entry-point.  Run with:
    uvicorn backend.main:app --reload
"""
from backend.api.routes import app  # noqa: F401 re-export for uvicorn
