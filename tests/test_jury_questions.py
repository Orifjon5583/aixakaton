"""
Regression tests for hackathon jury deep analytical queries:
1. Bot identity ('sen kimssan')
2. Default and cancellation risk analysis (Question #5)
3. Monopol spread & volatility analysis (Question #3)
4. Agricultural seasonality and correlation (Question #4)
"""

import pytest
from backend.app.services.gemini_service import gemini_service
from backend.app.services.sql_compiler import sql_compiler
from backend.app.db.connection import db_manager

def test_bot_identity():
    plan = gemini_service.generate_query_plan("sen kimssan", lang="uz")
    assert plan.is_out_of_scope is True
    assert "UZEX AI Analyst" in plan.out_of_scope_reason

def test_default_risk_analysis():
    q = "Kliring va bitimlarni bekor qilish (Defolt) xavfi tahlili: Ushbu davrda tuzilgan bitimlarning necha foizi majburiyatlar bajarilmagani sababli bekor qilingan yoki penya/jarima holatiga tushgan? Qaysi tovar toifalarida va qaysi hudud xaridorlari/sotuvchilari o‘rtasida to‘lov yoki yukni olib chiqib ketish bilan bog‘liq uzilishlar eng ko‘p qayd etilgan?"
    plan = gemini_service.generate_query_plan(q, lang="uz")
    assert plan.query_type == "DEFAULT_RISK_ANALYSIS"
    sql = sql_compiler.compile_plan(plan)
    db_res = db_manager.execute_safe_query(sql)
    assert db_res['success'] is True
    assert len(db_res['rows']) > 0
    ans = gemini_service.explain_results(q, plan, sql, db_res['columns'], db_res['rows'], lang="uz")
    assert "6.74%" in ans or "6,74%" in ans
    assert "Сахар белый" in ans

def test_spread_volatility_analysis():
    q = "Monopol tovarlar bo‘yicha spred va narx tebranishi (Volatillik): 2022–2026 yillar oralig‘ida avtobenzin (AI-80 va AI-92) hamda sement mahsulotlari bo‘yicha savdoga qo‘yilgan boshlang‘ich narx bilan yakuniy bitim narxi o‘rtasidagi o‘rtacha spred (%) qanday o‘zgardi? Narx oshishi eng yuqori bo‘lgan 3 ta asosiy davr (oy/mavsum) va ularning sabablari qanday?"
    plan = gemini_service.generate_query_plan(q, lang="uz")
    assert plan.query_type == "SPREAD_VOLATILITY_ANALYSIS"
    sql = sql_compiler.compile_plan(plan)
    db_res = db_manager.execute_safe_query(sql)
    assert db_res['success'] is True
    ans = gemini_service.explain_results(q, plan, sql, db_res['columns'], db_res['rows'], lang="uz")
    assert "0.93%" in ans
    assert "2023-yil" in ans

def test_agri_seasonality_analysis():
    q = "Bug‘doy, un va texnik paxta yog‘i/shroti bo‘yicha oylik savdo hajmlari hamda o‘rtacha kotirovkalar korrelyatsiyasi qanday? Qishloq xo‘jaligi hosil yig‘im-terim davri (avgust–noyabr) va bahor oylaridagi narx hamda bitimlar soni anomaliyalari qanday shakllangan?"
    plan = gemini_service.generate_query_plan(q, lang="uz")
    assert plan.query_type == "AGRI_SEASONALITY_ANALYSIS"
    sql = sql_compiler.compile_plan(plan)
    db_res = db_manager.execute_safe_query(sql)
    assert db_res['success'] is True
    ans = gemini_service.explain_results(q, plan, sql, db_res['columns'], db_res['rows'], lang="uz")
    assert "korrelyatsiya" in ans.lower()
    assert "avgust–noyabr" in ans

def test_export_commodity_audit():
    q = "2024-yilda eksport bitimlari bo’yicha dollardagi summasi eng katta bo’lgan tovarni aniqlang. Shu tovar uchun (barcha ro’yxatga olingan bitimlarni, bekor qilinganlarni ham qo’shib hisoblab) ayting: jami summa USD da, bitimlar soni, jami hajm va tortilgan o’rtacha narx (USD/birlik). So’ng: nechta bitim bekor qilingan va ularsiz summa qancha? Eng ko’p sotgan sotuvchining STIR raqami, nomi, summasi va umumiy summadagi ulushi qancha? Va yetkazib berilgan bitimlar orasida nechtasi shartnoma muddatidan kechikib yetkazilgan (soni va foizi), eng katta kechikish necha kun?"
    plan = gemini_service.generate_query_plan(q, lang="uz")
    assert plan.query_type == "EXPORT_COMMODITY_AUDIT"
    sql = sql_compiler.compile_plan(plan)
    db_res = db_manager.execute_safe_query(sql)
    assert db_res['success'] is True
    ans = gemini_service.explain_results(q, plan, sql, db_res['columns'], db_res['rows'], lang="uz")
    assert "КАТОД МЕДНЫЙ" in ans
    assert "98,824,607.77" in ans
    assert "917899526" in ans
    assert "385 ta bitim" in ans
    assert "24 ta bitim" in ans
    assert "18 kun" in ans
    assert "14 kun" in ans
