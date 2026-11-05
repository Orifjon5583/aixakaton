"""
Dataset Ingestion, Dynamic Schema Detection, and Quality Validation Service.
Complies with TZ Section 4. Supports CSV, XLSX, and JSON datasets.
"""

import os
import json
import pandas as pd
import duckdb
from typing import Dict, Any, List, Optional
from backend.app.db.connection import db_manager

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

class DatasetService:
    def __init__(self):
        self.db = db_manager

    def inspect_file(self, file_path: str) -> Dict[str, Any]:
        """
        Inspects an uploaded CSV, XLSX, or JSON file.
        Detects column types, null counts, duplicate records, and semantic roles.
        """
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.csv':
            df = pd.read_csv(file_path, nrows=5000)
            total_estimate = sum(1 for _ in open(file_path, 'rb')) - 1
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path, nrows=5000)
            total_estimate = len(df)
        elif ext == '.json':
            df = pd.read_json(file_path)
            total_estimate = len(df)
        else:
            raise ValueError(f"Qo'llab-quvvatlanmaydigan fayl formati: {ext}")

        # Schema detection
        columns_meta = []
        null_stats = {}
        for col in df.columns:
            dtype_str = str(df[col].dtype)
            null_count = int(df[col].isnull().sum())
            null_stats[col] = null_count
            unique_count = int(df[col].nunique())
            sample_vals = [str(x) for x in df[col].dropna().head(3).tolist()]
            
            semantic_role = self._detect_semantic_role(col, df[col])
            columns_meta.append({
                'name': col,
                'detected_type': dtype_str,
                'semantic_role': semantic_role,
                'null_count': null_count,
                'unique_count': unique_count,
                'sample_values': sample_vals
            })

        duplicates_sample = int(df.duplicated().sum())

        return {
            'is_valid': True,
            'file_name': os.path.basename(file_path),
            'total_rows_estimate': total_estimate,
            'columns': columns_meta,
            'null_statistics': null_stats,
            'duplicates_in_sample': duplicates_sample,
            'warnings': self._generate_quality_warnings(df, null_stats)
        }

    def _detect_semantic_role(self, col_name: str, series: pd.Series) -> str:
        name_lower = col_name.lower()
        
        # Date detection
        if any(w in name_lower for w in ['sana', 'date', 'kun', 'vaqt', 'time']):
            return 'deal_date'
        
        # Monetary amount / Price
        if any(w in name_lower for w in ['summa', 'amount', 'qiymat', 'narx', 'price']):
            return 'deal_amount'
            
        # Volume / Quantity
        if any(w in name_lower for w in ['hajm', 'volume', 'soni', 'miqdor', 'quantity', 'lot']):
            return 'quantity'

        # Identifiers (INN, Code, ID)
        if any(w in name_lower for w in ['inn', 'stir', 'kod', 'code', 'id']):
            return 'identifier'

        # Product / Commodity
        if any(w in name_lower for w in ['tovar', 'product', 'mahsulot', 'item']):
            return 'product_name'

        # Region / Location
        if any(w in name_lower for w in ['region', 'hudud', 'viloyat', 'shahar', 'ombor', 'warehouse']):
            return 'region'

        # Deal status
        if any(w in name_lower for w in ['status', 'holat', 'state']):
            return 'deal_status'

        # Company / Participant
        if any(w in name_lower for w in ['kompaniya', 'company', 'sotuvchi', 'xaridor', 'seller', 'buyer', 'korxona']):
            return 'company_name'

        return 'categorical'

    def _generate_quality_warnings(self, df: pd.DataFrame, null_stats: Dict[str, int]) -> List[str]:
        warnings = []
        for col, null_count in null_stats.items():
            pct = (null_count / len(df)) * 100
            if pct > 40:
                warnings.append(f"'{col}' ustunida {pct:.1f}% bo'sh (null) qiymatlar mavjud.")
        
        if df.duplicated().sum() > 0:
            warnings.append("Namunada takroriy (dublikat) qatorlar aniqlandi.")

        return warnings

dataset_service = DatasetService()
