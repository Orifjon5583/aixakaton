"""
Answer Validator and Question-Answer Alignment Enforcement for UZEX AI Analyst.
Ensures that all explicit user requirements (Company, Deals Count, Amount, Date Range)
are thoroughly analyzed, calculated via SQL, and validated before returning to the user.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel

class QuestionRequirements(BaseModel):
    wants_company: bool = False
    wants_deals_count: bool = False
    wants_amount: bool = False
    wants_volume: bool = False
    wants_price: bool = False
    wants_broker: bool = False
    wants_product: bool = False
    wants_region: bool = False
    
    # Target Entity / Subject
    has_target_subject: bool = False
    target_subject_raw: Optional[str] = None
    target_subject_kind: Optional[str] = None # 'region' | 'company' | 'broker' | 'not_found'
    target_region: Optional[str] = None
    target_company: Optional[str] = None
    subject_not_found: bool = False
    not_found_reason: Optional[str] = None

    # Ranking
    is_ranking: bool = False
    ranking_metric: Optional[str] = None # 'deals_count' | 'total_amount_uzs' | 'volume_units'
    ranking_limit: int = 1
    
    # Date Range
    year_range: Optional[List[int]] = None
    single_year: Optional[int] = None
    
    # Missing / Unsupported fields in question
    unsupported_fields: List[str] = []

def normalize_text(text: str) -> str:
    # Normalize all apostrophe variants: ‘, ’, ʼ, ʻ, `, ' to standard single quote '
    t = re.sub(r"[‘'’ʼʻ`]", "'", text.lower())
    # Normalize dashes: –, —, − to standard hyphen -
    t = re.sub(r"[–—−]", "-", t)
    return t

def extract_target_subject(question: str, lang: str = 'uz') -> Tuple[Optional[str], Optional[str], str]:
    """
    Extracts explicit subject/entity/qualifier from the question.
    Returns: (original_cased_subject, normalized_subject, language)
    """
    q_norm = normalize_text(question)

    # 1. Uzbek patterns
    # "X bilan tuzilgan (spot )?bitim" or "X ishtirokidagi bitim"
    m_bilan = re.search(r'([a-z0-9ʻʼ\'-]+(?:\s+[a-z0-9ʻʼ\'-]+){0,4}?)\s+(?:bilan\s+tuzilgan|ishtirokidagi|tomonidan\s+tuzilgan)\s+(?:spot\s+)?bitim', q_norm)
    if m_bilan:
        start, end = m_bilan.span(1)
        orig_subj = question[start:end].strip()
        orig_subj = re.sub(r'^(?:\d{4}-yilda|\d{4}\s+yilda|yilda)\s*', '', orig_subj, flags=re.IGNORECASE)
        norm_subj = normalize_text(orig_subj)
        return orig_subj, norm_subj, 'uz'

    # Planet / city / country patterns in Uzbek: e.g. "Mars sayyorasidagi kompaniyalar", "Parij shahridagi"
    m_loc_uz = re.search(r'([a-z0-9ʻʼ\'-]+(?:\s+[a-z0-9ʻʼ\'-]+){0,2}?)\s+(?:sayyorasidagi|sayyorasida|shahridagi|shahrida|davlatidagi|mamlakatidagi)(?:\s+(?:kompaniyalar|korxonalar|tashkilotlar|firmalar))?', q_norm)
    if m_loc_uz:
        start, end = m_loc_uz.span(0)
        orig_subj = question[start:end].strip()
        orig_subj = re.sub(r'^(?:\d{4}-yilda|\d{4}\s+yilda|yilda)\s*', '', orig_subj, flags=re.IGNORECASE)
        norm_subj = normalize_text(orig_subj)
        return orig_subj, norm_subj, 'uz'

    # "...dagi kompaniyalar"
    m_dagi = re.search(r'([a-z0-9ʻʼ\'-]+)dagi\s+(?:kompaniyalar|korxonalar|tashkilotlar|firmalar)', q_norm)
    if m_dagi:
        start, end = m_dagi.span(0)
        orig_subj = question[start:end].strip()
        norm_subj = normalize_text(orig_subj)
        return orig_subj, norm_subj, 'uz'

    # 2. Russian patterns
    # "сдел[окках] ... с X" or "заключенных ... с X"
    m_sdel_ru = re.search(r'(?:сдел[окках]+\s+(?:в\s+\d{4}\s+году\s+)?с|заключенн[ыхоеа-я]+\s+(?:в\s+\d{4}\s+году\s+)?с)\s+([а-яёa-z0-9\s]+?)(?:\s+(?:в|за|по|\d{4})|$|,|\.)', q_norm)
    if m_sdel_ru:
        start, end = m_sdel_ru.span(1)
        orig_subj = question[start:end].strip()
        norm_subj = normalize_text(orig_subj)
        return orig_subj, norm_subj, 'ru'

    m_loc_ru = re.search(r'(?:компани[ямиейях]+\s+)?(?:на\s+планете\s+[а-яёa-z0-9]+|в\s+городе\s+[а-яёa-z0-9]+|из\s+[а-яёa-z0-9]+)', q_norm)
    if m_loc_ru:
        start, end = m_loc_ru.span(0)
        orig_subj = question[start:end].strip()
        norm_subj = normalize_text(orig_subj)
        return orig_subj, norm_subj, 'ru'

    return None, None, lang

def check_subject_in_db(orig_subj: str, norm_subj: str, lang: str = 'uz') -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validates subject against official regions and DuckDB database tables.
    Returns: (exists_in_dataset, kind, message_or_mapped_value)
    """
    if not norm_subj:
        return True, None, None

    from backend.app.services.gemini_service import REGIONS_MAPPINGS
    from backend.app.db.connection import db_manager

    # 1. Check official 14 regions of Uzbekistan
    for reg_k, reg_v in REGIONS_MAPPINGS.items():
        if reg_k in norm_subj:
            return True, 'region', reg_v

    # 2. Clean subject to get search keywords
    clean_subj = re.sub(r'\b(kompaniyalar|kompaniyalari|korxonalar|korxonalari|tashkilotlar|firmalar|sayyorasidagi|sayyorasida|shahridagi|shahrida|davlatidagi|mamlakatidagi|viloyatidagi|viloyatida|компаниями|компании|на\s+планете|в\s+городе|из|в|сделок|сделки|spot|bitimlari|bitimlar)\b', ' ', norm_subj).strip()
    words = [w for w in clean_subj.split() if len(w) > 2]

    # 3. Check database (participants, brokers, deals)
    if not db_manager.is_demo and words:
        con = db_manager.get_connection()
        with db_manager.lock:
            for word in words:
                matched_p = con.execute("SELECT count(*) FROM participants WHERE name ILIKE ? OR region ILIKE ?", [f"%{word}%", f"%{word}%"]).fetchone()[0]
                if matched_p > 0:
                    return True, 'company', word
                matched_b = con.execute("SELECT count(*) FROM brokers WHERE name ILIKE ?", [f"%{word}%"]).fetchone()[0]
                if matched_b > 0:
                    return True, 'broker', word
                matched_d = con.execute("SELECT count(*) FROM deals WHERE region ILIKE ?", [f"%{word}%"]).fetchone()[0]
                if matched_d > 0:
                    return True, 'region', word

    # 4. If not found in any table or official region list, it does NOT exist in dataset!
    if lang == 'ru':
        msg = f"В предоставленном наборе данных информация о сделках с {orig_subj} не найдена."
    else:
        if 'bilan tuzilgan' in orig_subj:
            msg = f"Berilgan datasetda {orig_subj} haqida ma'lumot topilmadi."
        else:
            msg = f"Berilgan datasetda {orig_subj} bilan tuzilgan bitimlar haqida ma'lumot topilmadi."

    return False, 'not_found', msg

class AnswerValidator:
    def analyze_question(self, question: str, lang: str = 'uz') -> QuestionRequirements:
        """
        Deep semantic analysis of user question to extract all explicit requirements.
        Supports both Uzbek and Russian with full apostrophe and dash normalization.
        """
        q_lower = normalize_text(question)
        req = QuestionRequirements()

        is_macro_analysis = any(w in q_lower for w in [
            'defolt', 'дефолт', 'majburiyatlar bajarilmagani', 'bekor qilish', 'bekor qilingan', 'necha foizi',
            'spred', 'спред', 'volatillik', 'волатильность', 'boshlang\'ich narx', 'yakuniy bitim narxi',
            'korrelyatsiya', 'корреляция', 'hosil yig\'im', 'yig\'im-terim'
        ])

        # 1. Company requirement
        if not is_macro_analysis and any(w in q_lower for w in ['kompaniya', 'kompaniyani', 'sotuvchi', 'xaridor', 'korxona', 'tashkilot', 'компания', 'компанию', 'продавец', 'покупатель', 'предприятие']):
            req.wants_company = True

        # 2. Deals count requirement
        if any(w in q_lower for w in ['bitimlar soni', 'bitim soni', 'nechta bitim', 'jami bitimlar', 'bitim tuzgan', 'сделок', 'количество сделок', 'число сделок', 'сколько сделок']):
            req.wants_deals_count = True

        # 3. Monetary amount requirement
        if any(w in q_lower for w in ['umumiy qiymat', 'qiymati', 'qiymatini', 'summasi', 'summasini', 'aylanma', "so'mda", 'общая сумма', 'общий оборот', 'стоимость', 'сумме', 'сумму']):
            req.wants_amount = True

        # 4. Volume requirement
        if any(w in q_lower for w in ['hajm', 'hajmi', 'hajmini', 'qancha tonna', 'qancha sement', 'qancha bug', 'объем', 'тонн']):
            req.wants_volume = True

        # 5. Price requirement
        if any(w in q_lower for w in ["narx", "narxi", "o'rtacha narx", "narxini", "цена", "стоимость единицы", "средняя цена"]):
            req.wants_price = True

        # 6. Broker requirement
        if any(w in q_lower for w in ['broker', 'brokerlik', 'брокер', 'брокерская']) or re.search(r'\b(BK\d{3})\b', question, re.IGNORECASE):
            req.wants_broker = True

        # 7. Product requirement
        if any(w in q_lower for w in ['tovar', 'mahsulot', 'товар', 'продукция']):
            req.wants_product = True

        # 8. Ranking detection & metric determination
        if any(w in q_lower for w in ["eng ko'p", "eng kop", "eng katta", "eng yuqori", "yetakchi", "топ", "топ-", "top", "наибольш", "крупнейш", "лидер"]):
            req.is_ranking = True
            
            # Determine ranking limit
            limit_match = re.search(r'\b(?:top|топ)[ -]?(\d+)\b', q_lower)
            if limit_match:
                req.ranking_limit = int(limit_match.group(1))
            else:
                num_match = re.search(r'\b(\d+)\s*(?:ta|nafar)?\s*(?:kompaniya|sotuvchi|tovar|компани|продавц|товар)', q_lower)
                if num_match:
                    req.ranking_limit = int(num_match.group(1))
                else:
                    req.ranking_limit = 1

            # Determine ranking metric
            if any(w in q_lower for w in ['bitim tuzgan', 'bitimlar soni', 'bitim qilgan', 'по сделкам', 'по числу сделок', 'по количеству сделок']):
                req.ranking_metric = 'deals_count'
            elif any(w in q_lower for w in ['qiymat', 'summa', 'aylanma', 'по сумме', 'по обороту', 'по стоимости']):
                req.ranking_metric = 'total_amount_uzs'
            elif any(w in q_lower for w in ['hajm', 'sement sotgan', "bug'doy sotgan", 'paxta', 'по объему']):
                req.ranking_metric = 'volume_units'
            else:
                req.ranking_metric = 'deals_count'

        # 9. Year range detection (e.g. 2022-2026, 2022–2026, 2022 yildan 2026 yilgacha, с 2022 по 2026)
        range_match = re.search(r'\b(202[2-6])\s*(?:–|-|dan|yildan)\s*(202[2-6])(?:\s*gacha|\s*yilgacha|\s*oralig|\s*по)?\b', q_lower)
        if not range_match:
            range_match = re.search(r'с\s*(202[2-6])\s*по\s*(202[2-6])', q_lower)

        if range_match:
            start_y = int(range_match.group(1))
            end_y = int(range_match.group(2))
            if start_y <= end_y:
                req.year_range = list(range(start_y, end_y + 1))
            else:
                req.year_range = list(range(end_y, start_y + 1))
        else:
            single_years = [int(y) for y in re.findall(r'\b(202[0-9]|2030)\b', question)]
            if len(single_years) == 1:
                req.single_year = single_years[0]
            elif len(single_years) > 1:
                req.year_range = single_years

        # 10. Check for unsupported columns in question
        unsupported_keywords = [
            'xodim', 'ishchi', 'staff', 'сотрудник',
            'soliq', 'налог',
            'foyda', 'daromad', 'прибыль', 'доход',
            'manzil', 'telefon', 'email', 'телефон', 'адрес офиса',
            'rahbar', 'direktor', 'директор', 'руководитель'
        ]
        for uk in unsupported_keywords:
            if uk in q_lower:
                req.unsupported_fields.append(uk)

        # 11. Target Subject / Entity Extraction & Database Validation
        if not req.is_ranking:
            orig_s, norm_s, det_l = extract_target_subject(question, lang)
            if orig_s:
                req.has_target_subject = True
                req.target_subject_raw = orig_s
                exists, kind, val = check_subject_in_db(orig_s, norm_s, lang)
                req.target_subject_kind = kind
                if exists:
                    if kind == 'region':
                        req.target_region = val
                        req.wants_region = True
                    elif kind == 'company':
                        req.target_company = val
                        req.wants_company = True
                else:
                    req.subject_not_found = True
                    req.not_found_reason = val

        return req

    def validate_answer(self, question: str, req: QuestionRequirements, columns: List[str], rows: List[Any], answer_text: str, lang: str = 'uz') -> Tuple[bool, str, List[str]]:
        """
        Validates whether the generated answer fully and accurately satisfies ALL user requirements.
        If a requirement is missing from the data, explicitly identifies it.
        Returns: (is_fully_satisfied, corrected_or_augmented_answer, missing_requirements)
        """
        missing = []
        is_ru = (lang == 'ru')

        # Check 0: If target subject does not exist in dataset, strictly refuse to return unrelated stats or partial data
        if req.subject_not_found and req.not_found_reason:
            return False, req.not_found_reason, ["Target Subject Not Found"]

        # Check 1: If question requested company, is company name in the result and answer?
        has_company_col = any(c in columns for c in ['company_name', 'name', 'seller_name', 'buyer_name'])
        if req.wants_company and not has_company_col:
            if req.has_target_subject:
                # Primary subject is absent in results: cannot return unrelated general stats
                rejection = (
                    f"Berilgan datasetda {req.target_subject_raw} bilan tuzilgan bitimlar haqida ma'lumot topilmadi."
                    if not is_ru else
                    f"В предоставленном наборе данных информация о сделках с {req.target_subject_raw} не найдена."
                )
                return False, rejection, ["Target Subject Unmatched"]
            missing.append("Kompaniya nomi" if not is_ru else "Название компании")

        # Check 2: If question requested deals count, is it in result?
        has_count_col = any(c in columns for c in ['deals_count', 'total_deals', 'count_star()'])
        if req.wants_deals_count and not has_count_col:
            missing.append("Bitimlar soni" if not is_ru else "Количество сделок")

        # Check 3: If question requested total amount, is it in result?
        has_amount_col = any(c in columns for c in ['total_amount_uzs', 'amount_uzs', 'deal_amount_uzs'])
        if req.wants_amount and not has_amount_col:
            missing.append("Bitimlarning umumiy qiymati" if not is_ru else "Общая сумма сделок")

        # Check 4: Unsupported fields check
        if req.unsupported_fields:
            fields_str = ", ".join(f"'{f}'" for f in req.unsupported_fields)
            warning_msg = (
                f"\n\n⚠️ **Eslatma:** Quyidagi so'ralgan parametrlar ({fields_str}) datasetda mavjud emas."
                if not is_ru else
                f"\n\n⚠️ **Примечание:** Следующие запрошенные параметры ({fields_str}) отсутствуют в наборе данных."
            )
            answer_text += warning_msg

        # If any core requirement is missing
        if missing:
            missing_str = ", ".join(missing)
            msg = (
                f"\n\n⚠️ **Qisman javob:** Savoldagi quyidagi talablar bo'yicha ma'lumot to'liq aks ettirilmadi: {missing_str}."
                if not is_ru else
                f"\n\n⚠️ **Частичный ответ:** Следующие параметры запроса не были полностью отражены: {missing_str}."
            )
            return False, answer_text + msg, missing

        return True, answer_text, []

answer_validator = AnswerValidator()
