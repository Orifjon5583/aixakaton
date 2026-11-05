"""
System Health Router for UZEX AI Analyst.
"""

from fastapi import APIRouter
from backend.app.db.connection import db_manager

router = APIRouter(prefix="/api", tags=["Health"])

@router.get("/health")
def health():
    meta = db_manager.get_dataset_metadata()
    return {
        "status": "healthy",
        "service": "UZEX AI Analyst",
        "version": "2.0.0",
        "database": "DuckDB In-Memory Columnar",
        "dataset_loaded": meta['loaded'],
        "is_demo": meta['is_demo'],
        "total_deals": meta['total_deals']
    }
