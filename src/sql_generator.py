"""
Text-to-SQL Generator with multi-LLM support (Gemini, Groq, OpenAI) and Rule-based Fallback.
"""

import os
import sys
import re
from typing import Dict, Any, Tuple, Optional

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import (
    LLM_PROVIDER, GEMINI_API_KEY, OPENAI_API_KEY, GROQ_API_KEY,
    GEMINI_MODEL, OPENAI_MODEL, GROQ_MODEL, OPENAI_BASE_URL
)
from src.prompt_templates import SYSTEM_SQL_PROMPT, FEW_SHOT_EXAMPLES

class SQLGenerator:
    def __init__(self):
        self.provider = LLM_PROVIDER
        self._init_clients()

    def _init_clients(self):
        self.openai_client = None
        self.groq_client = None
        self.gemini_client = None

        if OPENAI_API_KEY:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(
                    api_key=OPENAI_API_KEY,
                    base_url=OPENAI_BASE_URL if OPENAI_BASE_URL else None
                )
            except Exception as e:
                print("OpenAI init warning:", e)

        if GROQ_API_KEY:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=GROQ_API_KEY)
            except Exception as e:
                print("Groq init warning:", e)

        if GEMINI_API_KEY:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
            except Exception as e:
                print("Gemini init warning:", e)

    def generate_sql(self, query: str, entities: Dict[str, Any]) -> Tuple[str, str]:
        """
        Generates DuckDB SQL from natural language query.
        Returns: (sql_query, explanation)
        """
        # First check if there is an explicit out-of-scope or non-existent entity warning
        if entities.get('warning_non_existent'):
            warnings_text = " | ".join(entities['warning_non_existent'])
            # Return a query that flags this clearly or check
            # But let's also allow a real query if partial
            pass

        # Try LLM first if available
        llm_sql = None
        if self.gemini_client and (self.provider == 'gemini' or not llm_sql):
            try:
                llm_sql = self._generate_gemini(query, entities)
            except Exception as e:
                print("Gemini generation error:", e)

        if not llm_sql and self.groq_client and (self.provider == 'groq' or not llm_sql):
            try:
                llm_sql = self._generate_groq(query, entities)
            except Exception as e:
                print("Groq generation error:", e)

        if not llm_sql and self.openai_client and (self.provider == 'openai' or not llm_sql):
            try:
                llm_sql = self._generate_openai(query, entities)
            except Exception as e:
                print("OpenAI generation error:", e)

        if llm_sql:
            clean_sql = self._clean_sql(llm_sql)
            if clean_sql:
                return clean_sql, "LLM orqali shakllantirildi"

        # Fallback to smart rule-based engine
        rule_sql = self._generate_rule_based(query, entities)
        return rule_sql, "Qoidalar va shablonlar asosida shakllantirildi"

    def _build_user_prompt(self, query: str, entities: Dict[str, Any]) -> str:
        prompt = f"Foydalanuvchi savoli: {query}\n\n"
        prompt += "Aniqlangan ob'ektlar (Entities):\n"
        if entities.get('inns'):
            prompt += f"- STIR/INN lar: {entities['inns']}\n"
        if entities.get('brokers'):
            prompt += f"- Brokerlar: {entities['brokers']}\n"
        if entities.get('years'):
            prompt += f"- Yillar: {entities['years']}\n"
        if entities.get('commodities'):
            prompt += f"- Tovar sinonimlari (ruscha bazadagi nomlar): {entities['commodities']}\n"
        if entities.get('regions'):
            prompt += f"- Hududlar: {entities['regions']}\n"
        if entities.get('deal_statuses'):
            prompt += f"- Bitim holatlari: {entities['deal_statuses']}\n"
        if entities.get('warning_non_existent'):
            prompt += f"- DIQQAT (Bazada mavjud emas deb belgilangan): {entities['warning_non_existent']}\n"

        prompt += "\nIltimos, ushbu savolga to'liq javob beruvchi DuckDB SQL so'rovini faqat ```sql ... ``` formatida qaytaring."
        return prompt

    def _generate_gemini(self, query: str, entities: Dict[str, Any]) -> Optional[str]:
        system_instruction = f"{SYSTEM_SQL_PROMPT}\n\n{FEW_SHOT_EXAMPLES}"
        user_content = self._build_user_prompt(query, entities)
        response = self.gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=user_content,
            config={
                'system_instruction': system_instruction,
                'temperature': 0.0,
            }
        )
        return response.text

    def _generate_groq(self, query: str, entities: Dict[str, Any]) -> Optional[str]:
        messages = [
            {"role": "system", "content": f"{SYSTEM_SQL_PROMPT}\n\n{FEW_SHOT_EXAMPLES}"},
            {"role": "user", "content": self._build_user_prompt(query, entities)}
        ]
        response = self.groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.0
        )
        return response.choices[0].message.content

    def _generate_openai(self, query: str, entities: Dict[str, Any]) -> Optional[str]:
        messages = [
            {"role": "system", "content": f"{SYSTEM_SQL_PROMPT}\n\n{FEW_SHOT_EXAMPLES}"},
            {"role": "user", "content": self._build_user_prompt(query, entities)}
        ]
        response = self.openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.0
        )
        return response.choices[0].message.content

    def _clean_sql(self, text: str) -> Optional[str]:
        if not text:
            return None
        # Extract from ```sql ... ```
        match = re.search(r'```(?:sql)?\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
        if match:
            clean = match.group(1).strip()
        else:
            clean = text.strip()

        # Remove trailing semicolons or commentary before/after
        clean = clean.strip('; \n\t')
        if clean.upper().startswith(('SELECT', 'WITH')):
            return clean
        return None

    def _generate_rule_based(self, query: str, entities: Dict[str, Any]) -> str:
        """
        Deterministic, high-accuracy SQL generation for standard patterns when LLM is unavailable.
        """
        q_lower = query.lower()
        years = entities.get('years', [])
        year_filter = f"deal_year = {years[0]}" if years else "1=1"
        commodities = entities.get('commodities', [])
        regions = entities.get('regions', [])
        deal_statuses = entities.get('deal_statuses', [])
        inns = entities.get('inns', [])
        brokers = entities.get('brokers', [])

        # 1. Broker info query: e.g. "BK001 kodi qaysi brokerga tegishli?"
        if brokers and ('qaysi broker' in q_lower or 'kodi' in q_lower or 'inn' in q_lower or 'stir' in q_lower or 'haqida' in q_lower):
            code = brokers[0]['broker_code']
            return f"SELECT broker_code, name, inn, region FROM brokers WHERE broker_code = '{code}'"

        # 2. Participant info query by INN
        if inns and ('kompaniya' in q_lower or 'stir' in q_lower or 'inn' in q_lower or 'haqida' in q_lower) and not commodities:
            inn = inns[0]['inn']
            return f"""
                SELECT 
                    p.inn, p.name, p.region, p.activity_type, p.role, p.vat_payer,
                    (SELECT count(*) FROM deals WHERE seller_inn = {inn}) AS deals_as_seller,
                    (SELECT count(*) FROM deals WHERE buyer_inn = {inn}) AS deals_as_buyer,
                    (SELECT coalesce(sum(deal_amount_uzs), 0) FROM deals WHERE seller_inn = {inn}) AS total_sold_uzs,
                    (SELECT coalesce(sum(deal_amount_uzs), 0) FROM deals WHERE buyer_inn = {inn}) AS total_bought_uzs
                FROM participants p
                WHERE p.inn = {inn}
            """

        # 3. Status queries: e.g. "bekor qilingan bitimlar"
        contract_types = entities.get('contract_types', [])
        if contract_types and ('eksport' in q_lower or 'экспорт' in q_lower or 'ichki' in q_lower):
            ct = contract_types[0]
            return f"""
                SELECT 
                    deal_year,
                    count(*) AS deals_count,
                    coalesce(sum(deal_amount_uzs), 0) AS total_sum_uzs,
                    coalesce(sum(deal_amount_raw), 0) AS total_amount_raw,
                    coalesce(sum(volume_units), 0) AS total_volume
                FROM deals
                WHERE contract_type = '{ct}'
                  AND {year_filter}
                GROUP BY deal_year
                ORDER BY deal_year
            """

        if deal_statuses:
            status = deal_statuses[0]
            region_clause = f"AND region = '{regions[0]}'" if regions else ""
            return f"""
                SELECT 
                    deal_year,
                    count(*) AS deals_count,
                    coalesce(sum(deal_amount_uzs), 0) AS total_sum_uzs,
                    coalesce(sum(volume_units), 0) AS total_volume
                FROM deals
                WHERE deal_status = '{status}'
                  AND {year_filter}
                  {region_clause}
                GROUP BY deal_year
                ORDER BY deal_year
            """

        # 4. Top sellers or top buyers
        if 'sotuvchi' in q_lower or 'продавец' in q_lower or 'sotgan' in q_lower:
            prod_cond = ""
            if commodities:
                conds = [f"product_name ILIKE '%{c}%'" for c in commodities]
                prod_cond = "AND (" + " OR ".join(conds) + ")"
            return f"""
                SELECT 
                    seller_inn,
                    seller_name,
                    sum(volume_units) AS total_volume,
                    unit,
                    sum(deal_amount_uzs) AS total_sum_uzs,
                    count(*) AS deals_count
                FROM v_deal_details
                WHERE {year_filter} {prod_cond}
                GROUP BY seller_inn, seller_name, unit
                ORDER BY total_volume DESC
                LIMIT 5
            """

        # 5. Top buyers
        if 'xaridor' in q_lower or 'покупатель' in q_lower or 'sotib olgan' in q_lower:
            prod_cond = ""
            if commodities:
                conds = [f"product_name ILIKE '%{c}%'" for c in commodities]
                prod_cond = "AND (" + " OR ".join(conds) + ")"
            return f"""
                SELECT 
                    buyer_inn,
                    buyer_name,
                    sum(volume_units) AS total_volume,
                    unit,
                    sum(deal_amount_uzs) AS total_sum_uzs,
                    count(*) AS deals_count
                FROM v_deal_details
                WHERE {year_filter} {prod_cond}
                GROUP BY buyer_inn, buyer_name, unit
                ORDER BY total_volume DESC
                LIMIT 5
            """

        # 6. Commodity volume & price query
        if commodities:
            conds = [f"product_name ILIKE '%{c}%'" for c in commodities]
            prod_clause = " AND (" + " OR ".join(conds) + ")"
            reg_clause = f" AND region = '{regions[0]}'" if regions else ""
            return f"""
                SELECT 
                    deal_year,
                    count(*) AS deals_count,
                    coalesce(sum(volume_units), 0) AS total_volume,
                    unit,
                    coalesce(avg(unit_price), 0) AS avg_unit_price,
                    coalesce(sum(deal_amount_uzs), 0) AS total_sum_uzs
                FROM deals
                WHERE {year_filter} {prod_clause} {reg_clause}
                GROUP BY deal_year, unit
                ORDER BY deal_year, total_volume DESC
                LIMIT 10
            """

        # 7. Region volume
        if regions:
            reg = regions[0]
            return f"""
                SELECT 
                    deal_year,
                    count(*) AS deals_count,
                    coalesce(sum(volume_units), 0) AS total_volume,
                    coalesce(sum(deal_amount_uzs), 0) AS total_sum_uzs
                FROM deals
                WHERE region = '{reg}' AND {year_filter}
                GROUP BY deal_year
                ORDER BY deal_year
            """

        # 8. General yearly overview
        return f"""
            SELECT 
                deal_year,
                count(*) AS total_deals,
                coalesce(sum(volume_units), 0) AS total_volume,
                coalesce(sum(deal_amount_uzs), 0) AS total_amount_uzs
            FROM deals
            WHERE {year_filter}
            GROUP BY deal_year
            ORDER BY deal_year
        """
