"""
Test user reported bug:
Question: "2022–2026-yillar oralig‘ida eng ko‘p bitim tuzgan kompaniyani aniqlang. Kompaniya nomi, jami bitimlar soni va bitimlarning umumiy qiymatini ko‘rsating."
"""

import sys
import io
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except Exception:
        pass

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_user_query():
    q = "2022–2026-yillar oralig‘ida eng ko‘p bitim tuzgan kompaniyani aniqlang. Kompaniya nomi, jami bitimlar soni va bitimlarning umumiy qiymatini ko‘rsating."
    resp = client.post('/api/chat', json={'message': q, 'lang': 'uz'})
    assert resp.status_code == 200
    data = resp.json()
    print("\n" + "="*70)
    print("SAVOL:", q)
    print("STATUS:", data['status'])
    print("JAVOB:\n", data['answer'])
    print("SQL:\n", data['provenance']['executed_sql'])
    print("="*70)

    # Verifications per user prompt:
    # 1. Company name must be returned
    assert "SITO‘TOM TEKSTIL MCHJ" in data['answer'] or "SITO" in data['answer']
    # 2. Deals count must be returned
    assert "12 147" in data['answer'] or "12147" in data['answer']
    # 3. Total amount must be returned
    assert "5 668 619" in data['answer'] or "5.67" in data['answer'] or "Trln" in data['answer']
    # 4. Must NOT return irrelevant 2022 single-year generic text
    assert "2022-yilda jami 183 605" not in data['answer']

if __name__ == '__main__':
    test_user_query()
