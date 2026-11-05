"""
Query History Router for UZEX AI Analyst.
Provides endpoints to fetch, export, and manage question audit logs.
"""

import csv
import io
from fastapi import APIRouter, Response
from typing import List, Dict, Any
from backend.app.services.history_service import history_service

router = APIRouter(prefix="/api/history", tags=["History"])

@router.get("", response_model=List[Dict[str, Any]])
def get_query_history(limit: int = 50):
    return history_service.get_recent_queries(limit=min(limit, 200))

@router.get("/export")
def export_history_csv():
    queries = history_service.get_recent_queries(limit=500)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Timestamp", "Language", "Question", "Answer", "Latency (ms)", "Status", "Rows Count", "Executed SQL"])
    
    for q in queries:
        writer.writerow([
            q["id"],
            q["created_at"],
            q["detected_lang"],
            q["question"],
            q["answer"],
            q["execution_time_ms"],
            q["status"],
            q["row_count"],
            q["executed_sql"] or ""
        ])
    
    csv_bytes = "\ufeff" + output.getvalue()
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=uzex_query_history.csv"}
    )

@router.delete("")
def clear_query_history():
    history_service.clear_history()
    return {"status": "cleared"}
