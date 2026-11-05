"""
Query History & Audit Service for UZEX AI Analyst.
Thread-safe persistence using SQLite for permanent question & answer logging.
"""

import os
import sqlite3
import threading
from typing import List, Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
HISTORY_DB_PATH = os.path.join(BASE_DIR, 'db', 'history.db')

class HistoryService:
    def __init__(self, db_path: str = HISTORY_DB_PATH):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS query_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        question TEXT NOT NULL,
                        detected_lang TEXT DEFAULT 'uz',
                        answer TEXT,
                        executed_sql TEXT,
                        execution_time_ms REAL DEFAULT 0.0,
                        status TEXT DEFAULT 'success',
                        row_count INTEGER DEFAULT 0
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_created ON query_history(created_at DESC)")
                conn.commit()
            finally:
                conn.close()

    def log_query(
        self,
        question: str,
        detected_lang: str,
        answer: str,
        executed_sql: Optional[str] = None,
        execution_time_ms: float = 0.0,
        status: str = 'success',
        row_count: int = 0
    ) -> int:
        """Saves a query event into the database safely."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO query_history (
                        question, detected_lang, answer, executed_sql,
                        execution_time_ms, status, row_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    question.strip(),
                    detected_lang,
                    answer,
                    executed_sql,
                    execution_time_ms,
                    status,
                    row_count
                ))
                conn.commit()
                return cursor.lastrowid
            except Exception as e:
                print("Error logging query to history:", e)
                return -1
            finally:
                conn.close()

    def get_recent_queries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent queries ordered by newest first."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, created_at, question, detected_lang, answer, 
                           executed_sql, execution_time_ms, status, row_count
                    FROM query_history
                    ORDER BY id DESC
                    LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                return [
                    {
                        "id": r[0],
                        "created_at": r[1],
                        "question": r[2],
                        "detected_lang": r[3],
                        "answer": r[4],
                        "executed_sql": r[5],
                        "execution_time_ms": r[6],
                        "status": r[7],
                        "row_count": r[8]
                    }
                    for r in rows
                ]
            finally:
                conn.close()

    def clear_history(self) -> bool:
        """Clears all query history."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM query_history")
                conn.commit()
                return True
            finally:
                conn.close()

history_service = HistoryService()
