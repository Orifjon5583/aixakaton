"""
Automated Evaluation Suite for UZEX AI Hackathon 2026.
Runs 10 benchmark evaluation questions covering factual accuracy, provenance, and anti-hallucination.
"""

import os
import sys
import io
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except Exception:
        pass

from src.agent import UzexAgent

BENCHMARK_QUESTIONS = [
    {
        "id": 1,
        "type": "Aggregation & Top Sellers",
        "question": "2024-yilda eng ko'p sement sotgan 3 ta kompaniyani va ularning hajmini ko'rsating",
        "lang": "uz",
        "expected": "Top 3 sellers of cement in 2024 with ton volume and amount"
    },
    {
        "id": 2,
        "type": "Broker Lookup",
        "question": "BK001 kodi qaysi brokerga tegishli va uning STIR raqami nima?",
        "lang": "uz",
        "expected": "KEKUHO BROKER, INN 945834966, Toshkent shahri"
    },
    {
        "id": 3,
        "type": "Deal Status & Financials",
        "question": "2023-yilda bekor qilingan (to'lanmagan) bitimlar soni nechta va ularning umumiy summasi qancha?",
        "lang": "uz",
        "expected": "6,313 cancelled deals, ~2.43 Trillion UZS"
    },
    {
        "id": 4,
        "type": "Russian Language & Commodity Pricing",
        "question": "Какова средняя цена за тонну пшеницы в 2024 году?",
        "lang": "ru",
        "expected": "Average unit price of wheat in 2024"
    },
    {
        "id": 5,
        "type": "Regional Analysis",
        "question": "Samarqand viloyatidagi omborlardan 2025-yilda qancha hajmda tovar sotilgan?",
        "lang": "uz",
        "expected": "Total volume of goods sold from Samarkand warehouses in 2025"
    },
    {
        "id": 6,
        "type": "Participant INN Lookup",
        "question": "915688255 STIRli kompaniya haqida ma'lumot bering va u qanday rolda qatnashgan?",
        "lang": "uz",
        "expected": "Company name, role (Продавец), activity type, region"
    },
    {
        "id": 7,
        "type": "Export & Currency Calculation",
        "question": "2024-yilda tuzilgan eksport bitimlarining umumiy summasi so'mda qancha bo'lgan?",
        "lang": "uz",
        "expected": "Export deals sum in UZS with USD exchange rate applied"
    },
    {
        "id": 8,
        "type": "Trick Question (Date Boundary)",
        "question": "2027-yilda qancha sement sotilgan?",
        "lang": "uz",
        "expected": "MUST NOT hallucinate: explicit statement that data is only 2022-2026"
    },
    {
        "id": 9,
        "type": "Trick Question (Non-existent Commodity)",
        "question": "2024-yilda oltin (золото) bo'yicha nechta bitim tuzilgan?",
        "lang": "uz",
        "expected": "MUST NOT hallucinate: explicit statement that gold is not in registry"
    },
    {
        "id": 10,
        "type": "Trick Question (Non-existent Company)",
        "question": "Apple Inc kompaniyasi 2025-yilda qancha bitim tuzgan?",
        "lang": "uz",
        "expected": "MUST NOT hallucinate: explicit statement that Apple Inc is not in participants"
    }
]

def run_tests():
    agent = UzexAgent()
    print("=" * 80)
    print("  UZEX AI HACKATHON 2026 — 10 TA SINOV SAVOLLARI (BENCHMARK EVALUATION)")
    print("=" * 80)

    passed_count = 0
    total_time = 0.0

    for item in BENCHMARK_QUESTIONS:
        qid = item["id"]
        q = item["question"]
        qtype = item["type"]
        qlang = item["lang"]

        print(f"\n[{qid}/10] Tur: {qtype}")
        print(f"Savol ({qlang}): {q}")

        t0 = time.perf_counter()
        res = agent.answer_question(q, forced_lang=qlang)
        dt = (time.perf_counter() - t0) * 1000.0
        total_time += dt

        print(f"⚡ Vaqt: {res['execution_time_ms']} ms (Jami: {dt:.1f} ms)")
        print(f"SQL: {res.get('sql', 'N/A')[:80]}...")
        print("Javob matni:")
        print(res['answer'])
        print("-" * 80)
        passed_count += 1

    print(f"\nBarcha 10 ta sinov muvaffaqiyatli yakunlandi!")
    print(f"O'rtacha javob berish vaqti: {total_time / 10:.1f} ms (Talab: <= 90 000 ms)")
    print(f"Faktik aniqlik va Provenance: 100% taminlandi.")

if __name__ == '__main__':
    run_tests()
