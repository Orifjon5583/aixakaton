"""
FastAPI Backend for UZEX AI Birja Bitimlari.
Serves AI query engine, statistics, and static frontend assets.
"""

import os
import sys
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Ensure project root in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from src.agent import UzexAgent

app = FastAPI(title="UZEX AI Birja Bitimlari API", version="1.0.0")

# Enable CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = UzexAgent()

class QueryRequest(BaseModel):
    query: str
    lang: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    sql: str
    columns: List[str]
    rows: List[Any]
    row_count: int
    execution_time_ms: float
    entities: Dict[str, Any]
    is_empty_or_warning: bool

@app.get("/api/health")
def health_check():
    return {"status": "ok", "database": "DuckDB active", "deals": 500000}

@app.post("/api/query", response_model=QueryResponse)
def execute_query(req: QueryRequest):
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    result = agent.answer_question(req.query, forced_lang=req.lang)
    return QueryResponse(
        answer=result['answer'],
        sql=result.get('sql', ''),
        columns=result.get('columns', []),
        rows=result.get('rows', []),
        row_count=result.get('row_count', 0),
        execution_time_ms=result.get('execution_time_ms', 0.0),
        entities=result.get('entities', {}),
        is_empty_or_warning=result.get('is_empty_or_warning', False)
    )

@app.get("/api/stats")
def get_stats():
    con = agent.db_engine.get_connection()
    yearly = con.execute("""
        SELECT 
            deal_year,
            count(*) as deals_count,
            round(sum(deal_amount_uzs) / 1e12, 2) as amount_trln,
            round(sum(volume_units) / 1e6, 2) as volume_mln
        FROM deals
        GROUP BY deal_year
        ORDER BY deal_year
    """).df().to_dict(orient="records")

    top_commodities = con.execute("""
        SELECT 
            product_name,
            count(*) as deals_count,
            round(sum(deal_amount_uzs) / 1e9, 2) as amount_mlrd
        FROM deals
        GROUP BY product_name
        ORDER BY count(*) DESC
        LIMIT 8
    """).df().to_dict(orient="records")

    statuses = con.execute("""
        SELECT deal_status, count(*) as count
        FROM deals
        GROUP BY deal_status
        ORDER BY count DESC
    """).df().to_dict(orient="records")

    return {
        "total_deals": 500000,
        "total_contracts": 6616,
        "total_participants": 14392,
        "total_brokers": 120,
        "yearly": yearly,
        "top_commodities": top_commodities,
        "statuses": statuses
    }

# Mount static files if frontend build exists
FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_react_app(full_path: str):
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=True)
