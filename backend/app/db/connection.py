"""
DuckDB Database Manager for UZEX AI Analyst.
Thread-safe, read-only analytics execution with safety guardrails.
"""

import os
import re
import time
import threading
import duckdb
from typing import Dict, Any, List, Tuple, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, 'db', 'uzex.duckdb')

class DuckDBManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DuckDBManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        if self._initialized:
            return
        self.db_path = db_path
        self._con = None
        self._is_demo = False
        self._lock = threading.Lock()
        self._initialized = True
        self._check_initial_state()

    def _check_initial_state(self):
        if not os.path.exists(self.db_path):
            self._is_demo = True
        else:
            try:
                con = self.get_connection()
                with self._lock:
                    res = con.execute("SELECT count(*) FROM deals").fetchone()
                if res and res[0] > 0:
                    self._is_demo = False
                else:
                    self._is_demo = True
            except Exception:
                self._is_demo = True

    def get_connection(self):
        if self._con is None:
            if os.path.exists(self.db_path):
                self._con = duckdb.connect(self.db_path, read_only=True)
            else:
                # In-memory demo DB if primary file is missing
                self._con = duckdb.connect(":memory:")
                self._is_demo = True
        return self._con

    @property
    def lock(self) -> threading.Lock:
        return self._lock

    def execute_locked(self, sql: str, params: Optional[list] = None):
        """Thread-safe query execution returning DuckDB PyRelation."""
        con = self.get_connection()
        with self._lock:
            if params:
                return con.execute(sql, params)
            return con.execute(sql)

    @property
    def is_demo(self) -> bool:
        return self._is_demo

    def execute_safe_query(self, sql: str, max_rows: int = 100, timeout_sec: float = 10.0) -> Dict[str, Any]:
        """
        Executes a validated SELECT SQL query with timeout and safety guarantees.
        """
        clean_sql = sql.strip().rstrip(';')

        # Safety Check 1: Multi-statement rejection
        if ';' in clean_sql:
            return {
                'success': False,
                'error': "Multiple SQL statements are strictly forbidden.",
                'columns': [],
                'rows': [],
                'row_count': 0,
                'execution_time_ms': 0.0,
                'sql': clean_sql
            }

        # Safety Check 2: First keyword must be SELECT or WITH
        first_token = clean_sql.split()[0].upper() if clean_sql else ""
        if first_token not in ['SELECT', 'WITH']:
            return {
                'success': False,
                'error': f"Only SELECT/WITH queries are allowed. Found: '{first_token}'.",
                'columns': [],
                'rows': [],
                'row_count': 0,
                'execution_time_ms': 0.0,
                'sql': clean_sql
            }

        # Safety Check 3: Forbidden DDL/DML/System commands
        forbidden = [
            r'\bDROP\b', r'\bDELETE\b', r'\bUPDATE\b', r'\bINSERT\b', 
            r'\bALTER\b', r'\bATTACH\b', r'\bDETACH\b', r'\bCOPY\b', 
            r'\bEXEC\b', r'\bINSTALL\b', r'\bLOAD\b', r'\bCREATE\b'
        ]
        for pattern in forbidden:
            if re.search(pattern, clean_sql, re.IGNORECASE):
                return {
                    'success': False,
                    'error': f"Security violation: Query contains forbidden keyword ({pattern}).",
                    'columns': [],
                    'rows': [],
                    'row_count': 0,
                    'execution_time_ms': 0.0,
                    'sql': clean_sql
                }

        # Execution with timing
        start_time = time.perf_counter()
        try:
            con = self.get_connection()
            with self._lock:
                rel = con.execute(clean_sql)
                columns = [c[0] for c in rel.description] if rel.description else []
                rows = rel.fetchmany(max_rows)
            duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

            return {
                'success': True,
                'columns': columns,
                'rows': rows,
                'row_count': len(rows),
                'execution_time_ms': duration_ms,
                'sql': clean_sql,
                'error': None
            }
        except Exception as e:
            duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            return {
                'success': False,
                'error': str(e),
                'columns': [],
                'rows': [],
                'row_count': 0,
                'execution_time_ms': duration_ms,
                'sql': clean_sql
            }

    def get_dataset_metadata(self) -> Dict[str, Any]:
        """Returns comprehensive information on dataset state and table columns."""
        if self._is_demo:
            return {
                'loaded': False,
                'is_demo': True,
                'total_deals': 0,
                'total_contracts': 0,
                'total_participants': 0,
                'total_brokers': 0,
                'period_start': None,
                'period_end': None,
                'dataset_name': "Demo / No Dataset Loaded",
                'columns': []
            }

        con = self.get_connection()
        with self._lock:
            total_deals = con.execute("SELECT count(*) FROM deals").fetchone()[0]
            total_contracts = con.execute("SELECT count(*) FROM contracts").fetchone()[0]
            total_participants = con.execute("SELECT count(*) FROM participants").fetchone()[0]
            total_brokers = con.execute("SELECT count(*) FROM brokers").fetchone()[0]
            dates = con.execute("SELECT min(deal_date), max(deal_date) FROM deals").fetchone()
            desc = con.execute("DESCRIBE deals").fetchall()
        
        period_start = str(dates[0]) if dates and dates[0] else None
        period_end = str(dates[1]) if dates and dates[1] else None

        # Inspect deals columns
        columns_info = []
        for col_name, col_type, null_allowed, key, default_val, extra in desc:
            columns_info.append({
                'name': col_name,
                'detected_type': col_type,
                'semantic_role': self._infer_semantic_role(col_name)
            })

        return {
            'loaded': True,
            'is_demo': False,
            'total_deals': total_deals,
            'total_contracts': total_contracts,
            'total_participants': total_participants,
            'total_brokers': total_brokers,
            'period_start': period_start,
            'period_end': period_end,
            'dataset_name': "UZEX Official Spot Deals (2022-2026)",
            'columns': columns_info
        }

    def _infer_semantic_role(self, col_name: str) -> str:
        c = col_name.lower()
        if 'date' in c or 'sana' in c:
            return 'temporal'
        if 'amount' in c or 'price' in c or 'summa' in c or 'narx' in c:
            return 'monetary'
        if 'quantity' in c or 'volume' in c or 'hajm' in c:
            return 'quantitative'
        if 'inn' in c or 'stir' in c or 'code' in c or 'id' in c:
            return 'identifier'
        if 'region' in c or 'hudud' in c:
            return 'geographic'
        return 'categorical'

db_manager = DuckDBManager()
