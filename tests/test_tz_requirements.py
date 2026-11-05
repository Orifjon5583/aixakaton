"""
Comprehensive Test Suite for UZEX AI Analyst.
Covers all 15 mandatory test cases defined in TZ Section 14.
"""

import os
import sys
import io
import time
import pytest
from fastapi.testclient import TestClient

# Ensure root in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except Exception:
        pass

from backend.app.main import app
from backend.app.db.connection import db_manager
from backend.app.validators.query_validator import MSG_NO_DATA, MSG_COLUMN_NOT_FOUND

client = TestClient(app)

def test_01_simple_uzbek_question():
    """1. O‘zbekcha oddiy savol"""
    resp = client.post("/api/chat", json={"message": "2024-yilda nechta bitim tuzilgan?", "lang": "uz"})
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == 'success'
    assert "106 647" in data['answer'] or "106647" in data['answer']
    assert data['provenance']['execution_time_ms'] < 5000.0

def test_02_simple_russian_question():
    """2. Ruscha oddiy savol"""
    resp = client.post("/api/chat", json={"message": "Сколько сделок было заключено в 2023 году?", "lang": "ru"})
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == 'success'
    assert "93 985" in data['answer'] or "93985" in data['answer']

def test_03_yearly_statistics():
    """3. Yillik statistika"""
    resp = client.get("/api/analytics/years")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 5 # 2022, 2023, 2024, 2025, 2026
    years = [item['deal_year'] for item in data]
    assert 2022 in years and 2026 in years

def test_04_compare_two_years():
    """4. Ikki yil taqqoslash"""
    resp = client.post("/api/chat", json={"message": "2022 va 2026-yillarni taqqosla", "lang": "uz"})
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == 'success'
    assert data['data_table'] is not None
    assert len(data['data_table']['rows']) >= 2

def test_05_top_10_companies():
    """5. TOP-10 kompaniya"""
    resp = client.get("/api/analytics/top-companies?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) <= 10
    assert len(data) > 0
    assert data[0]['total_amount_uzs'] > 0

def test_06_top_10_products():
    """6. TOP-10 tovar"""
    resp = client.get("/api/analytics/top-products?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) <= 10
    assert len(data) > 0
    assert "product_name" in data[0]

def test_07_non_existent_company():
    """7. Mavjud bo‘lmagan kompaniya"""
    resp = client.post("/api/chat", json={"message": "Apple Inc kompaniyasi 2024-yilda qancha xarid qilgan?", "lang": "uz"})
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == 'out_of_scope'
    assert "topilmadi" in data['answer'] or "mavjud emas" in data['answer']

def test_08_non_existent_commodity():
    """8. Mavjud bo‘lmagan tovar (Oltin)"""
    resp = client.post("/api/chat", json={"message": "2024-yilda oltin bo'yicha nechta bitim tuzilgan?", "lang": "uz"})
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == 'out_of_scope'
    assert "mavjud emas" in data['answer'] or "topilmadi" in data['answer']

def test_09_missing_column_or_field():
    """9. Datasetda yo‘q ustun"""
    # Ask about non-existent metric like bitcoin or exchange rate of euro
    resp = client.post("/api/chat", json={"message": "Euro kursi bo'yicha bitimlar qancha?", "lang": "uz"})
    assert resp.status_code == 200
    data = resp.json()
    # Must not hallucinate!
    assert data['status'] in ['no_data', 'out_of_scope']

def test_10_empty_dataset_or_no_result():
    """10. Natija topilmagan holat (No result fallback)"""
    resp = client.post("/api/chat", json={"message": "999999999 STIRli kompaniyaning bitimlari", "lang": "uz"})
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] in ['no_data', 'out_of_scope']
    assert (MSG_NO_DATA['uz'] in data['answer']) or ("topilmadi" in data['answer'])

def test_11_duplicate_records_distinct_handling():
    """11. Takroriy bitimlar va DISTINCT tekshiruvi"""
    con = db_manager.get_connection()
    total_deals = con.execute("SELECT count(*) FROM deals").fetchone()[0]
    distinct_deals = con.execute("SELECT count(DISTINCT deal_id) FROM deals").fetchone()[0]
    # Each deal_id must be completely unique
    assert total_deals == distinct_deals == 500000

def test_12_out_of_range_date():
    """12. Noto‘g‘ri sana (2027-yil)"""
    resp = client.post("/api/chat", json={"message": "2027-yilda qancha sement sotilgan?", "lang": "uz"})
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == 'out_of_scope'
    assert "2027" in data['answer']
    assert "2022" in data['answer']

def test_13_sql_injection_defense():
    """13. SQL injection hujumlaridan himoya"""
    malicious = "2024-yil; DROP TABLE deals; --"
    resp = client.post("/api/chat", json={"message": malicious, "lang": "uz"})
    assert resp.status_code == 200
    # Must not drop table!
    con = db_manager.get_connection()
    cnt = con.execute("SELECT count(*) FROM deals").fetchone()[0]
    assert cnt == 500000

def test_14_gemini_fallback_reliability():
    """14. Gemini API ishlamasa ham to'g'ri ishlashi"""
    # Force client = None to test deterministic engine
    from backend.app.services.gemini_service import gemini_service
    orig_client = gemini_service.client
    try:
        gemini_service.client = None
        resp = client.post("/api/chat", json={"message": "BK001 kodi qaysi brokerga tegishli?", "lang": "uz"})
        assert resp.status_code == 200
        data = resp.json()
        assert data['status'] == 'success'
        assert "BK001" in data['answer']
        assert "945834966" in data['answer'] or "945 834 966" in data['answer']
    finally:
        gemini_service.client = orig_client

def test_15_performance_with_500k_records():
    """15. 500 000 ta yozuv bilan ishlash tezligi (Talab: <= 90s, Amalda: < 0.2s)"""
    t0 = time.perf_counter()
    resp = client.get("/api/analytics/overview")
    dt = time.perf_counter() - t0
    assert resp.status_code == 200
    data = resp.json()
    assert data['total_deals'] == 500000
    assert dt < 1.0 # Executed in less than 1 second!

def test_16_user_complex_multi_requirement_question():
    """16. Murakkab ko'p talabli savol (Kompaniya + Bitimlar soni + Umumiy qiymat + Yillar oralig'i)"""
    q = "2022–2026-yillar oralig‘ida eng ko‘p bitim tuzgan kompaniyani aniqlang. Kompaniya nomi, jami bitimlar soni va bitimlarning umumiy qiymatini ko‘rsating."
    resp = client.post("/api/chat", json={"message": q, "lang": "uz"})
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == 'success'
    ans = data['answer']
    # Must contain company name
    assert "SITO‘TOM TEKSTIL MCHJ" in ans or "SITO" in ans
    # Must contain deals count
    assert "12 147" in ans or "12147" in ans
    # Must contain total amount
    assert "5 668 619" in ans or "5.67" in ans or "Trln" in ans
    # Must NOT contain unrelated single-year statistic
    assert "2022-yilda jami 183 605" not in ans

def test_17_mars_sayyorasi_relevance_validation():
    """17. Savol mazmuniga moslik (Query Relevance): Mars sayyorasidagi kompaniyalar rad etilishi"""
    # Uzbek
    q_uz = "2023-yilda Mars sayyorasidagi kompaniyalar bilan tuzilgan spot bitimlari soni va umumiy qiymatini ko‘rsating."
    resp_uz = client.post("/api/chat", json={"message": q_uz, "lang": "uz"})
    assert resp_uz.status_code == 200
    data_uz = resp_uz.json()
    assert data_uz['status'] == 'out_of_scope'
    assert "36 616 596 290 597" not in data_uz['answer']
    assert "Berilgan datasetda Mars sayyorasidagi kompaniyalar bilan tuzilgan bitimlar haqida ma'lumot topilmadi." in data_uz['answer']

    # Russian
    q_ru = "Покажите количество и общую сумму спот-сделок в 2023 году с компаниями на планете Марс."
    resp_ru = client.post("/api/chat", json={"message": q_ru, "lang": "ru"})
    assert resp_ru.status_code == 200
    data_ru = resp_ru.json()
    assert data_ru['status'] == 'out_of_scope'
    assert "36 616 596 290 597" not in data_ru['answer']
    assert ("не найдена" in data_ru['answer'] or "не найден" in data_ru['answer'])

if __name__ == '__main__':
    print("Barcha testlarni ishga tushirmoqdamiz...")
    pytest.main(["-v", __file__])
