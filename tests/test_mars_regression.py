"""
Regression Test for Query Relevance Validation and Fictitious Entity Rejection.
Specifically covers:
"2023-yilda Mars sayyorasidagi kompaniyalar bilan tuzilgan spot bitimlari soni va umumiy qiymatini ko‘rsating."
and Russian counterpart.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.gemini_service import gemini_service
from backend.app.validators.query_validator import query_validator
from backend.app.validators.answer_validator import answer_validator
from backend.app.services.sql_compiler import sql_compiler
from backend.app.db.connection import db_manager

def test_mars_sayyorasi_uzbek_rejection():
    """
    CRITICAL REGRESSION TEST:
    Savol: "2023-yilda Mars sayyorasidagi kompaniyalar bilan tuzilgan spot bitimlari soni va umumiy qiymatini ko‘rsating."
    Kutiladigan javob: "Berilgan datasetda Mars sayyorasidagi kompaniyalar bilan tuzilgan bitimlar haqida ma'lumot topilmadi."
    """
    question = "2023-yilda Mars sayyorasidagi kompaniyalar bilan tuzilgan spot bitimlari soni va umumiy qiymatini ko‘rsating."
    lang = "uz"

    # Step 1: Query plan generation
    plan = gemini_service.generate_query_plan(question, lang=lang)

    # Must be marked out_of_scope
    assert plan.is_out_of_scope is True
    assert "Mars sayyorasidagi kompaniyalar" in plan.out_of_scope_reason
    assert "ma'lumot topilmadi" in plan.out_of_scope_reason

    # Step 2: Query validator rejection
    is_valid, reason = query_validator.validate_plan(plan, lang=lang, question=question)
    assert is_valid is False
    assert reason == "Berilgan datasetda Mars sayyorasidagi kompaniyalar bilan tuzilgan bitimlar haqida ma'lumot topilmadi."

def test_mars_sayyorasi_russian_rejection():
    """
    Russian test for fictitious planet Mars:
    "Покажите количество и общую сумму спот-сделок в 2023 году с компаниями на планете Марс."
    """
    question = "Покажите количество и общую сумму спот-сделок в 2023 году с компаниями на планете Марс."
    lang = "ru"

    plan = gemini_service.generate_query_plan(question, lang=lang)
    assert plan.is_out_of_scope is True

    is_valid, reason = query_validator.validate_plan(plan, lang=lang, question=question)
    assert is_valid is False
    assert "не найдена" in reason or "не найден" in reason
    assert "Марс" in reason or "марс" in reason

def test_no_partial_data_on_unrelated_stats():
    """
    Ensures that AnswerValidator NEVER tags completely irrelevant statistics as PARTIAL_DATA.
    """
    question = "2023-yilda Mars sayyorasidagi kompaniyalar bilan tuzilgan spot bitimlari soni va umumiy qiymatini ko‘rsating."
    req = answer_validator.analyze_question(question, lang='uz')

    assert req.subject_not_found is True
    assert "Mars sayyorasidagi kompaniyalar" in req.not_found_reason

    # If someone tried to pass general 2023 stats as answer:
    fake_columns = ['deals_count', 'total_amount_uzs']
    fake_rows = [[183605, 36616596290597.7]]
    fake_answer = "2023-yilda bitimlarning umumiy qiymati 36 616 596 290 597.70 so‘m."

    is_sat, val_answer, missing = answer_validator.validate_answer(
        question=question,
        req=req,
        columns=fake_columns,
        rows=fake_rows,
        answer_text=fake_answer,
        lang='uz'
    )

    # Must be completely rejected, NOT marked partial data with 36 Trillion UZS!
    assert is_sat is False
    assert "36 616 596 290 597" not in val_answer
    assert "Berilgan datasetda Mars sayyorasidagi kompaniyalar bilan tuzilgan bitimlar haqida ma'lumot topilmadi." in val_answer

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
