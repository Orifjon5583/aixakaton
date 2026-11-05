"""
Anti-Hallucination and Query Plan Validator for UZEX AI Analyst.
Guarantees zero hallucinations, enforces strict dataset boundaries, and checks schema compliance.
"""

from typing import Dict, Any, Tuple, Optional
from backend.app.models.schemas import QueryPlan
from backend.app.db.connection import db_manager

# Mandatory rejection phrases from TZ Section 7 with strict Anti-Hallucination guarantees
MSG_NO_DATA = {
    'uz': "Berilgan ma'lumotlar bazasida ushbu savolga javob topilmadi. Men o‘zimdan taxmin qila olmayman — faqat aniq faktik manbaga va tasdiqlangan birja ma'lumotlariga tayanaman.",
    'ru': "В предоставленной базе данных не найден ответ на данный вопрос. Я не могу делать предположения или отвечать от себя — я опираюсь исключительно на точные фактические данные биржи."
}

MSG_COLUMN_NOT_FOUND = {
    'uz': "Ushbu ma'lumot datasetda mavjud emas.",
    'ru': "Данное поле отсутствует в предоставленном наборе данных."
}

# Known non-traded items on spot exchange to prevent trick hallucinations
NON_TRADED_ITEMS = [
    'oltin', 'золото', 'kumush', 'серебро', 
    'neft', 'нефть сырая', 'gaz', 'природный газ', 
    'dollar sotib olish', 'bitcoin', 'kriptovalyuta'
]

# Valid dataset bounds
VALID_YEAR_RANGE = (2022, 2026)

class QueryValidator:
    def __init__(self):
        self.db = db_manager

    def validate_plan(self, plan: QueryPlan, lang: str = 'uz', question: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Validates QueryPlan against active dataset schema and anti-hallucination rules.
        Returns: (is_valid, rejection_reason_if_any)
        """
        # 0. Question semantic check for fictitious entities, planets, foreign cities
        if question:
            from backend.app.validators.answer_validator import answer_validator
            req = answer_validator.analyze_question(question, lang)
            if req.subject_not_found and req.not_found_reason:
                return False, req.not_found_reason

        # 1. Out of Scope flag from plan
        if plan.is_out_of_scope:
            reason = plan.out_of_scope_reason or MSG_NO_DATA.get(lang, MSG_NO_DATA['uz'])
            return False, reason

        # 2. Year boundaries check (2022 - 2026)
        if plan.filters.years:
            for y in plan.filters.years:
                if y < VALID_YEAR_RANGE[0] or y > VALID_YEAR_RANGE[1]:
                    if lang == 'ru':
                        return False, f"В данных нет информации за {y} год. Набор данных биржи охватывает только период с 2022 по 2026 год (по 30 октября 2026 г.)."
                    return False, f"Bazada {y}-yil uchun ma'lumot yo'q. Birja ma'lumotlari faqat 2022–2026 yillarni (2026-yil 30-oktabrgacha) qamrab olgan."

        # 3. Non-traded commodity check
        if plan.filters.product_name:
            p_name = plan.filters.product_name.lower()
            for item in NON_TRADED_ITEMS:
                if item in p_name:
                    if lang == 'ru':
                        return False, f"Товар '{item}' отсутствует в реестре биржевых спот-сделок. Данные по нему не найдены."
                    return False, f"'{item}' tovari birja spot bitimlari reyestrida mavjud emas. Ushbu tovar bo'yicha ma'lumot yo'q."

        # 4. Check region validity if specified
        if plan.filters.region and not self.db.is_demo:
            from backend.app.services.gemini_service import REGIONS_MAPPINGS
            valid_regions = set(REGIONS_MAPPINGS.values())
            if plan.filters.region not in valid_regions:
                con = self.db.get_connection()
                with self.db.lock:
                    r_match = con.execute("SELECT count(*) FROM deals WHERE region ILIKE ?", [f"%{plan.filters.region}%"]).fetchone()[0]
                if r_match == 0:
                    if lang == 'ru':
                        return False, f"В предоставленном наборе данных регион '{plan.filters.region}' не найден."
                    return False, f"Berilgan datasetda '{plan.filters.region}' hududi bo'yicha ma'lumot topilmadi."

        # 5. Check company existence if specific company name is provided
        if plan.filters.company_name and not self.db.is_demo:
            con = self.db.get_connection()
            name_pattern = f"%{plan.filters.company_name}%"
            with self.db.lock:
                matched = con.execute("SELECT count(*) FROM participants WHERE name ILIKE ?", [name_pattern]).fetchone()[0]
                if matched == 0:
                    matched_b = con.execute("SELECT count(*) FROM brokers WHERE name ILIKE ?", [name_pattern]).fetchone()[0]
                else:
                    matched_b = 0

            if matched == 0 and matched_b == 0:
                if lang == 'ru':
                    return False, f"В предоставленном наборе данных информация о сделках с {plan.filters.company_name} не найдена."
                return False, f"Berilgan datasetda {plan.filters.company_name} bilan tuzilgan bitimlar haqida ma'lumot topilmadi."

        # 6. Check broker code format if provided
        if plan.filters.broker_code and not self.db.is_demo:
            code = plan.filters.broker_code.upper()
            con = self.db.get_connection()
            with self.db.lock:
                b_exists = con.execute("SELECT count(*) FROM brokers WHERE broker_code = ?", [code]).fetchone()[0]
            if b_exists == 0:
                if lang == 'ru':
                    return False, f"Брокерский код '{code}' отсутствует в базе данных (коды от BK001 до BK120)."
                return False, f"'{code}' broker kodi bazada mavjud emas (broker kodlari BK001 dan BK120 gacha)."

        return True, None

query_validator = QueryValidator()
