"""
Entity Resolution and Fuzzy Matching for UZEX Birja Bitimlari.
Matches participants, brokers, products, regions, and dates from natural language questions (Uzbek/Russian).
"""

import re
import sys
import io
import duckdb
import os
from typing import Dict, List, Any, Optional

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except Exception:
        pass

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db', 'uzex.duckdb')

# Commodity synonyms matching by word stem or term
COMMODITY_SYNONYMS = {
    # Cement
    'sement': ['цемент', 'портландцемент'],
    'цемент': ['цемент', 'портландцемент'],
    'портландцемент': ['портландцемент'],
    
    # Wheat & Flour
    "bug'doy": ['пшеница', 'пшеница продовольственная'],
    "bugdoy": ['пшеница', 'пшеница продовольственная'],
    'bug‘doy': ['пшеница', 'пшеница продовольственная'],
    'пшениц': ['пшеница', 'пшеница продовольственная'],
    'пшеница': ['пшеница', 'пшеница продовольственная'],
    'un': ['мука', 'мука пшеничная'],
    'uni': ['мука', 'мука пшеничная'],
    'мук': ['мука', 'мука пшеничная'],
    'мука': ['мука', 'мука пшеничная'],
    
    # Cotton & Derivatives
    'paxta': ['хлопок', 'хлопок-сырец', 'хлопок сырец', 'волокно хлопковое'],
    'paxta tolasi': ['волокно хлопковое', 'хлопковое волокно', 'хлопок'],
    'paxta chigiti': ['семена хлопчатника', 'семена хлопковые'],
    'paxta yog‘i': ['масло хлопковое'],
    'paxta yogi': ['масло хлопковое'],
    "paxta yog'i": ['масло хлопковое'],
    'shrot': ['шрот', 'шрот хлопковых семян'],
    'шрот': ['шрот', 'шрот хлопковых семян'],
    'хлопк': ['хлопок', 'хлопок-сырец', 'хлопок сырец', 'волокно хлопковое'],
    'хлопок': ['хлопок', 'хлопок-сырец', 'хлопок сырец', 'волокно хлопковое'],
    'хлопок-сырец': ['хлопок-сырец', 'хлопок сырец'],
    
    # Sugar & Oil
    'shakar': ['сахар', 'сахар-песок'],
    'сахар': ['сахар', 'сахар-песок'],
    'yog‘': ['масло хлопковое', 'масло подсолнечное'],
    'yogi': ['масло хлопковое', 'масло подсолнечное'],
    'масл': ['масло хлопковое', 'масло подсолнечное'],
    'масло': ['масло хлопковое', 'масло подсолнечное'],
    'guruch': ['рис', 'рис шлифованный'],
    'рис': ['рис', 'рис шлифованный'],
    
    # Fuels & Petrochemicals
    'benzin': ['бензин', 'автобензин', 'бензин автомобильный'],
    'avtobenzin': ['бензин', 'автобензин', 'бензин автомобильный'],
    'бензин': ['бензин', 'автобензин', 'бензин автомобильный'],
    'дизел': ['дизельное топливо', 'дизель'],
    'дизель': ['дизельное топливо', 'дизель'],
    'dizel': ['дизельное топливо', 'дизель'],
    'solyarka': ['дизельное топливо'],
    'bitum': ['битум', 'битум нефтяной'],
    'битум': ['битум', 'битум нефтяной'],
    'kerosin': ['керосин'],
    'керосин': ['керосин'],
    'polietilen': ['полиэтилен'],
    'полиэтилен': ['полиэтилен'],
    'polipropilen': ['полипропилен'],
    'полипропилен': ['полипропилен'],
    
    # Fertilizers & Chemicals
    'karbamid': ['карбамид'],
    'карбамид': ['карбамид'],
    'selitra': ['аммиачная селитра', 'селитра'],
    'селитра': ['аммиачная селитра', 'селитра'],
    'ammiak': ['аммиак'],
    'аммиак': ['аммиак'],
    'oltingugurt': ['сера', 'сера техническая'],
    'сера': ['сера', 'сера техническая'],
    
    # Metals & Construction
    'metall': ['прокат', 'металлопрокат', 'арматура'],
    'armatura': ['арматура', 'прокат'],
    'прокат': ['прокат', 'металлопрокат', 'арматура'],
    'арматура': ['арматура', 'прокат'],
    'alyuminiy': ['алюминий'],
    'алюминий': ['алюминий'],
    'mis': ['медь'],
    'медь': ['медь'],
    'ko‘mir': ['уголь', 'уголь каменный'],
    "ko'mir": ['уголь', 'уголь каменный'],
    'komir': ['уголь', 'уголь каменный'],
    'угол': ['уголь', 'уголь каменный'],
    'уголь': ['уголь', 'уголь каменный'],
    'ohak': ['известь'],
    'известь': ['известь'],
    'g‘isht': ['кирпич'],
    'gisht': ['кирпич'],
    'кирпич': ['кирпич'],
    'taxta': ['пиломатериалы', 'доска'],
    'yog‘och': ['пиломатериалы', 'древесина'],
    'пиломатериалы': ['пиломатериалы'],
}

# Standardized 14 regions mapping
REGION_MAPPINGS = {
    'andijon': 'Andijon viloyati',
    'андижан': 'Andijon viloyati',
    'buxoro': 'Buxoro viloyati',
    'бухар': 'Buxoro viloyati',
    'farg‘ona': 'Farg‘ona viloyati',
    "farg'ona": 'Farg‘ona viloyati',
    'ферган': 'Farg‘ona viloyati',
    'jizzax': 'Jizzax viloyati',
    'джизак': 'Jizzax viloyati',
    'namangan': 'Namangan viloyati',
    'наманган': 'Namangan viloyati',
    'navoiy': 'Navoiy viloyati',
    'навои': 'Navoiy viloyati',
    'qashqadaryo': 'Qashqadaryo viloyati',
    'кашкадарь': 'Qashqadaryo viloyati',
    'qoraqalpog‘iston': 'Qoraqalpog‘iston Respublikasi',
    "qoraqalpog'iston": 'Qoraqalpog‘iston Respublikasi',
    'каракалпак': 'Qoraqalpog‘iston Respublikasi',
    'samarqand': 'Samarqand viloyati',
    'самарканд': 'Samarqand viloyati',
    'sirdaryo': 'Sirdaryo viloyati',
    'сырдарь': 'Sirdaryo viloyati',
    'surxondaryo': 'Surxondaryo viloyati',
    'сурхандарь': 'Surxondaryo viloyati',
    'toshkent viloyat': 'Toshkent viloyati',
    'ташкентская область': 'Toshkent viloyati',
    'toshkent shahar': 'Toshkent shahri',
    'toshkent shahri': 'Toshkent shahri',
    'город ташкент': 'Toshkent shahri',
    'г. ташкент': 'Toshkent shahri',
    'xorazm': 'Xorazm viloyati',
    'хорезм': 'Xorazm viloyati',
}

# Deal Status mappings
DEAL_STATUS_MAPPINGS = {
    'ijro etilgan': 'Исполнен',
    'bajarilgan': 'Исполнен',
    'yetkazilgan': 'Исполнен',
    'исполнен': 'Исполнен',
    'bekor qilingan': 'Аннулирован(Не оплачен)',
    'to‘lanmagan': 'Аннулирован(Не оплачен)',
    'annul': 'Аннулирован(Не оплачен)',
    'аннулирован': 'Аннулирован(Не оплачен)',
    'qisman ijro': 'Исполнен(Частично)',
    'qisman': 'Исполнен(Частично)',
    'частично': 'Исполнен(Частично)',
    'to‘langan': 'Оплачен',
    'tolangan': 'Оплачен',
    'оплачен': 'Оплачен',
    'kutilmoqda': 'Ждёт оплату',
    'kutmoqda': 'Ждёт оплату',
    'ждет оплату': 'Ждёт оплату',
    'ждёт оплату': 'Ждёт оплату',
    'imzolangan': 'Заключен',
    'tuzilgan': 'Заключен',
    'заключен': 'Заключен',
    'yangi': 'Новый',
    'новый': 'Новый',
    'imzolanmagan': 'Не подписан',
    'не подписан': 'Не подписан',
}

class EntityIndexer:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._con = None
        self.brokers_map = {}
        self.participants_cache = []
        self._load_caches()

    def _get_con(self):
        if self._con is None:
            self._con = duckdb.connect(self.db_path, read_only=True)
        return self._con

    def _load_caches(self):
        con = self._get_con()
        # Brokers
        rows = con.execute("SELECT broker_code, name, inn, region FROM brokers").fetchall()
        for code, name, inn, reg in rows:
            self.brokers_map[code.upper()] = {
                'broker_code': code,
                'name': name,
                'inn': inn,
                'region': reg
            }
            # Also index by normalized name
            clean_name = re.sub(r'["\'«»“”]', '', name).strip().lower()
            self.brokers_map[clean_name] = self.brokers_map[code.upper()]

    def resolve_entities(self, query: str) -> Dict[str, Any]:
        """
        Extracts and resolves all entities in a query:
        - INNs (9-digit numbers)
        - Broker codes (BK001-BK120)
        - Contract IDs (6-digit starting with 1)
        - Deal IDs
        - Years & Date ranges
        - Matched commodities and synonyms
        - Matched regions
        - Matched deal statuses
        - Explicit non-existent checks
        """
        q_lower = query.lower()
        res = {
            'inns': [],
            'brokers': [],
            'contract_ids': [],
            'deal_ids': [],
            'years': [],
            'commodities': [],
            'regions': [],
            'deal_statuses': [],
            'warning_non_existent': []
        }

        # 1. 9-digit INNs
        inns = re.findall(r'\b(\d{9})\b', query)
        con = self._get_con()
        for inn in inns:
            p = con.execute("SELECT inn, name, region, activity_type, role FROM participants WHERE inn = ?", [int(inn)]).fetchone()
            if p:
                res['inns'].append({
                    'inn': p[0],
                    'name': p[1],
                    'region': p[2],
                    'activity_type': p[3],
                    'role': p[4]
                })
            else:
                b = con.execute("SELECT broker_code, name, inn, region FROM brokers WHERE inn = ?", [int(inn)]).fetchone()
                if b:
                    res['brokers'].append({
                        'broker_code': b[0],
                        'name': b[1],
                        'inn': b[2],
                        'region': b[3]
                    })
                else:
                    res['warning_non_existent'].append(f"STIR/ИНН {inn} базада мавжуд эмас / отсутствует в базе")

        # 2. Broker Codes (BK001 - BK120)
        bk_codes = re.findall(r'\b(BK\d{3})\b', query, re.IGNORECASE)
        for bk in bk_codes:
            code = bk.upper()
            if code in self.brokers_map:
                res['brokers'].append(self.brokers_map[code])
            else:
                res['warning_non_existent'].append(f"Брокер коди {code} мавжуд эмас")

        # 3. Years (2020 - 2030)
        years = re.findall(r'\b(202[0-9]|2030)\b', query)
        for y in set(years):
            year_int = int(y)
            res['years'].append(year_int)
            if year_int < 2022 or year_int > 2026:
                res['warning_non_existent'].append(
                    f"Йил {year_int}: Маълумотлар фақат 2022-2026 йиллар учун мавжуд (2022.01.03 - 2026.10.30)."
                )

        # 4. Regions
        for key, reg in REGION_MAPPINGS.items():
            if key in q_lower:
                if reg not in res['regions']:
                    res['regions'].append(reg)

        # If user just said "toshkent" without specifying "shahar" or "viloyat", include both
        if 'toshkent' in q_lower or 'ташкент' in q_lower:
            if not res['regions']:
                res['regions'].extend(['Toshkent shahri', 'Toshkent viloyati'])

        # 5. Deal Statuses & Contract Types
        res['contract_types'] = []
        if 'eksport' in q_lower or 'экспорт' in q_lower:
            res['contract_types'].append('Экспортный')
        elif 'ichki' in q_lower or 'внутренн' in q_lower:
            res['contract_types'].append('Внутренний')

        for key, status in DEAL_STATUS_MAPPINGS.items():
            if key in q_lower and 'eksport' not in q_lower and 'экспорт' not in q_lower:
                if status not in res['deal_statuses']:
                    res['deal_statuses'].append(status)

        # 6. Commodities / Products matching
        for term, syns in COMMODITY_SYNONYMS.items():
            if term in q_lower:
                for s in syns:
                    if s not in res['commodities']:
                        res['commodities'].append(s)

        # 7. Check for known non-traded items on Spot exchange
        non_existent_check = ['oltin', 'золото', 'kumush', 'серебро', 'neft', 'нефть сырая', 'gaz', 'природный газ', 'dollar sotib olish']
        for ne in non_existent_check:
            if ne in q_lower:
                res['warning_non_existent'].append(
                    f"'{ne}' бўйича биржада маълумот мавжуд эмас (товар спот реестрида йўқ)."
                )

        # 8. Check for company name mentions in quotes or with keyword 'kompaniya', 'компания'
        candidates = re.findall(r'["«“]([^"»”]+)["»”]', query)
        
        # Also check without quotes: e.g. "Apple Inc kompaniyasi", "Artel kompaniyasi"
        comp_match = re.findall(r'\b([A-Z][A-Za-z0-9\s]+?)\s+(?:kompaniyasi|korxonasi|firmasi|компания|фирма)\b', query)
        for cm in comp_match:
            cm_clean = cm.strip()
            if len(cm_clean) >= 3 and cm_clean not in candidates:
                candidates.append(cm_clean)

        for q_str in candidates:
            clean_q = q_str.strip()
            # Check if this company exists in participants or brokers
            matched = con.execute("""
                SELECT inn, name, role, region FROM participants 
                WHERE name ILIKE ? OR name ILIKE ?
                LIMIT 3
            """, [f"%{clean_q}%", f"\"{clean_q}\"%"]).fetchall()
            if matched:
                for m in matched:
                    res['inns'].append({'inn': m[0], 'name': m[1], 'role': m[2], 'region': m[3]})
            else:
                # Check brokers
                matched_b = con.execute("""
                    SELECT broker_code, name, inn, region FROM brokers 
                    WHERE name ILIKE ?
                    LIMIT 2
                """, [f"%{clean_q}%"]).fetchall()
                if matched_b:
                    for mb in matched_b:
                        res['brokers'].append({'broker_code': mb[0], 'name': mb[1], 'inn': mb[2], 'region': mb[3]})
                else:
                    res['warning_non_existent'].append(
                        f"'{clean_q}' номли компания ёки брокер реестрда топилмади."
                    )

        return res

if __name__ == '__main__':
    indexer = EntityIndexer()
    test_queries = [
        "2024-yilda eng ko'p sement sotgan 3 ta kompaniya",
        "BK001 kodi qaysi brokerga tegishli?",
        "915688255 STIRli sotuvchining 2023-yildagi bitimlari",
        "2027-yilda qancha bug'doy sotilgan?",
        "Samarqand viloyatida 2025-yilda bekor qilingan bitimlar soni",
        "Oltin bo'yicha 2024-yilda qancha bitim tuzilgan?"
    ]
    for tq in test_queries:
        print("\nQ:", tq)
        print("Resolved:", indexer.resolve_entities(tq))
