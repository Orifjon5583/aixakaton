"""
Dataset Status and Admin Ingestion Router for UZEX AI Analyst.
Conforms to TZ Section 4 and Section 15.
"""

import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.app.db.connection import db_manager
from backend.app.services.dataset_service import dataset_service, UPLOAD_DIR
from backend.app.models.schemas import (
    DatasetStatusResponse, SchemaConfirmRequest, DatasetValidationResponse, ColumnMetadata
)

router = APIRouter(prefix="/api", tags=["Dataset Admin"])

@router.get("/dataset/status", response_model=DatasetStatusResponse)
def get_dataset_status():
    meta = db_manager.get_dataset_metadata()
    cols = [ColumnMetadata(**c) for c in meta.get('columns', [])]
    return DatasetStatusResponse(
        loaded=meta['loaded'],
        is_demo=meta['is_demo'],
        total_deals=meta['total_deals'],
        total_contracts=meta['total_contracts'],
        total_participants=meta['total_participants'],
        total_brokers=meta['total_brokers'],
        period_start=meta['period_start'],
        period_end=meta['period_end'],
        dataset_name=meta['dataset_name'],
        columns=cols
    )

@router.post("/admin/upload")
async def upload_dataset(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Fayl tanlanmagan.")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.csv', '.xlsx', '.xls', '.json']:
        raise HTTPException(status_code=400, detail="Faqat CSV, XLSX yoki JSON fayllar qabul qilinadi.")

    dest_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Automatic inspection
    try:
        inspection = dataset_service.inspect_file(dest_path)
        return {
            "status": "uploaded",
            "message": f"'{file.filename}' muvaffaqiyatli yuklandi va tahlil qilindi.",
            "inspection": inspection
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Faylni tahlil qilishda xatolik: {str(e)}")

@router.post("/admin/validate", response_model=DatasetValidationResponse)
def validate_dataset(file_name: str):
    file_path = os.path.join(UPLOAD_DIR, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Ko'rsatilgan fayl topilmadi.")

    inspection = dataset_service.inspect_file(file_path)
    return DatasetValidationResponse(
        is_valid=inspection['is_valid'],
        total_rows=inspection['total_rows_estimate'],
        columns_detected=[c['name'] for c in inspection['columns']],
        null_statistics=inspection['null_statistics'],
        duplicate_count=inspection['duplicates_in_sample'],
        warnings=inspection['warnings']
    )

@router.post("/admin/schema/confirm")
def confirm_schema(req: SchemaConfirmRequest):
    return {
        "status": "confirmed",
        "message": f"{len(req.column_mappings)} ta ustun mappingi tasdiqlandi.",
        "mappings": req.column_mappings
    }
