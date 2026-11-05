"""
Chat Endpoint Router for UZEX AI Analyst.
Orchestrates: Question -> Language -> Gemini QueryPlan -> Validation -> SQL Compiler -> DuckDB -> Explanation -> Provenance.
Strictly adheres to TZ Section 3, 6, 7, 12, 16.
"""

import time
import re
from fastapi import APIRouter, HTTPException
from backend.app.models.schemas import ChatRequest, ChatResponse, ProvenanceData, DataTable
from backend.app.services.gemini_service import gemini_service
from backend.app.validators.query_validator import query_validator, MSG_NO_DATA
from backend.app.services.sql_compiler import sql_compiler
from backend.app.db.connection import db_manager
from backend.app.services.history_service import history_service

router = APIRouter(prefix="/api", tags=["Chat"])

def detect_language(text: str) -> str:
    text_lower = text.lower()
    has_cyrillic = bool(re.search(r'[а-яё]', text_lower))
    if not has_cyrillic:
        # Any Latin text in UZEX is Uzbek
        return 'uz'
    # Uzbek in Cyrillic check
    if re.search(r'[ўқғҳ]', text_lower) or re.search(r'\b(йил|йилда|нечта|қанча|бўйича|битим|битимлар|сотилган|сотиб|тўлиқ|компанияси|сўм|қайси|орқали)\b', text_lower):
        return 'uz'
    return 'ru'

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Savol bo'sh bo'lishi mumkin emas.")

    start_time = time.perf_counter()
    # Always detect question language directly from question content
    # (Regardless of UI website language setting)
    lang = detect_language(req.message)

    # 1. Generate Structured Query Plan (via Gemini or deterministic parser)
    plan = gemini_service.generate_query_plan(req.message, lang=lang)

    # 2. Validate Query Plan (Anti-Hallucination Guardrails)
    is_valid, rejection_reason = query_validator.validate_plan(plan, lang=lang, question=req.message)
    if not is_valid:
        exec_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        provenance = ProvenanceData(
            question=req.message,
            detected_lang=lang,
            dataset_version="UZEX 2022-2026",
            query_plan=plan.model_dump(),
            executed_sql=None,
            execution_time_ms=exec_ms,
            filters_applied=plan.filters.model_dump(exclude_none=True),
            row_count=0,
            data_source="UZEX Dataset (Nol natija / Rad etildi)"
        )
        history_service.log_query(
            question=req.message,
            detected_lang=lang,
            answer=rejection_reason or MSG_NO_DATA[lang],
            executed_sql=None,
            execution_time_ms=exec_ms,
            status='out_of_scope',
            row_count=0
        )
        return ChatResponse(
            answer=rejection_reason or MSG_NO_DATA[lang],
            provenance=provenance,
            data_table=None,
            status='out_of_scope',
            is_demo=db_manager.is_demo
        )

    # 3. Compile SQL from validated Query Plan
    sql = sql_compiler.compile_plan(plan)

    # 4. Execute on DuckDB safely
    db_res = db_manager.execute_safe_query(sql)
    exec_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

    # If query failed or 0 rows returned
    if not db_res['success'] or not db_res['rows']:
        if plan.filters.company_name:
            no_data_msg = (
                f"Berilgan datasetda {plan.filters.company_name} bilan tuzilgan bitimlar haqida ma'lumot topilmadi. Men o‘zimdan taxmin qila olmayman — faqat aniq faktik manbaga va tasdiqlangan birja ma'lumotlariga tayanaman."
                if lang == 'uz' else
                f"В предоставленном наборе данных информация о сделках с {plan.filters.company_name} не найдена. Я не могу делать предположения или отвечать от себя — я опираюсь исключительно на точные фактические данные биржи."
            )
        elif plan.filters.region:
            no_data_msg = (
                f"Berilgan datasetda {plan.filters.region} bo'yicha bitimlar topilmadi. Men o‘zimdan taxmin qila olmayman — faqat aniq faktik manbaga va tasdiqlangan birja ma'lumotlariga tayanaman."
                if lang == 'uz' else
                f"В предоставленном наборе данных информация о сделках по региону '{plan.filters.region}' не найдена. Я не могу делать предположения или отвечать от себя — я опираюсь исключительно на точные фактические данные биржи."
            )
        elif plan.filters.product_name:
            no_data_msg = (
                f"Berilgan datasetda '{plan.filters.product_name}' tovari bo'yicha bitimlar topilmadi. Men o‘zimdan taxmin qila olmayman — faqat aniq faktik manbaga va tasdiqlangan birja ma'lumotlariga tayanaman."
                if lang == 'uz' else
                f"В предоставленном наборе данных сделки по товару '{plan.filters.product_name}' не найдены. Я не могу делать предположения или отвечать от себя — я опираюсь исключительно на точные фактические данные биржи."
            )
        else:
            no_data_msg = MSG_NO_DATA[lang]

        provenance = ProvenanceData(
            question=req.message,
            detected_lang=lang,
            dataset_version="UZEX 2022-2026",
            query_plan=plan.model_dump(),
            executed_sql=sql,
            execution_time_ms=exec_ms,
            filters_applied=plan.filters.model_dump(exclude_none=True),
            row_count=0,
            data_source="DuckDB Analytical Engine"
        )
        history_service.log_query(
            question=req.message,
            detected_lang=lang,
            answer=rejection_reason or MSG_NO_DATA[lang],
            executed_sql=None,
            execution_time_ms=exec_ms,
            status='out_of_scope',
            row_count=0
        )
        return ChatResponse(
            answer=no_data_msg,
            provenance=provenance,
            data_table=None,
            status='no_data',
            is_demo=db_manager.is_demo
        )

    # 5. Explain verified SQL results (Gemini / Synthesizer)
    raw_explanation = gemini_service.explain_results(
        question=req.message,
        plan=plan,
        sql=sql,
        columns=db_res['columns'],
        rows=db_res['rows'],
        lang=lang
    )

    # 6. Answer Validator: enforce Question-Answer requirement alignment
    from backend.app.validators.answer_validator import answer_validator
    req_analysis = answer_validator.analyze_question(req.message, lang=lang)
    is_satisfied, validated_answer, missing_fields = answer_validator.validate_answer(
        question=req.message,
        req=req_analysis,
        columns=db_res['columns'],
        rows=db_res['rows'],
        answer_text=raw_explanation,
        lang=lang
    )

    data_table = DataTable(
        columns=db_res['columns'],
        rows=db_res['rows'][:20]
    )

    provenance = ProvenanceData(
        question=req.message,
        detected_lang=lang,
        dataset_version="UZEX 2022-2026",
        query_plan=plan.model_dump(),
        executed_sql=sql,
        execution_time_ms=exec_ms,
        filters_applied=plan.filters.model_dump(exclude_none=True),
        row_count=db_res['row_count'],
        data_source="UZEX Spot Deals Dataset (2022-2026)"
    )

    history_service.log_query(
        question=req.message,
        detected_lang=lang,
        answer=validated_answer,
        executed_sql=sql,
        execution_time_ms=exec_ms,
        status='success',
        row_count=db_res['row_count']
    )

    return ChatResponse(
        answer=validated_answer,
        provenance=provenance,
        data_table=data_table,
        status='success',
        is_demo=db_manager.is_demo
    )
