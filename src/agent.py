"""
Core AI Agent for UZEX Birja Bitimlari.
Integrates Entity Resolution, Text-to-SQL, Safe Execution, Anti-Hallucination Guardrails, and Provenance Formatting.
"""

import os
import sys
import io
import re
import time
from typing import Dict, Any, Optional, List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except Exception:
        pass

from src.entity_indexer import EntityIndexer
from src.db_engine import DatabaseEngine
from src.sql_generator import SQLGenerator
from src.config import (
    LLM_PROVIDER, GEMINI_API_KEY, OPENAI_API_KEY, GROQ_API_KEY,
    GEMINI_MODEL, OPENAI_MODEL, GROQ_MODEL, OPENAI_BASE_URL
)
from src.prompt_templates import SYSTEM_ANSWER_PROMPT

class UzexAgent:
    def __init__(self):
        self.entity_indexer = EntityIndexer()
        self.db_engine = DatabaseEngine()
        self.sql_generator = SQLGenerator()
        self._init_llm_clients()

    def _init_llm_clients(self):
        self.openai_client = self.sql_generator.openai_client
        self.groq_client = self.sql_generator.groq_client
        self.gemini_client = self.sql_generator.gemini_client

    def detect_language(self, text: str) -> str:
        """
        Detects whether text is primarily Uzbek ('uz') or Russian ('ru').
        """
        # Uzbek specific indicators
        uz_patterns = [
            r"\b(haqida|qancha|nechta|qaysi|bo'yicha|bo‘yicha|yil|yildagi|bitim|bitimlar|sotilgan|sotib|kompaniya|STIR|so'm|so‘m|tuzilgan|bekor|narxi|eng|ko'p|bajarilgan)\b",
            r"[o‘o'g‘g']",
            r"\b(va|bilan|uchun|ham)\b"
        ]
        text_lower = text.lower()
        uz_score = sum(len(re.findall(p, text_lower)) for p in uz_patterns)
        
        # Russian specific indicators
        ru_patterns = [
            r"[а-яё]",
            r"\b(сколько|какой|какая|какие|было|сделок|сделки|цена|товар|компания|продавец|покупатель|сумма|рублей|сумов|году|года|всего|наиболее)\b"
        ]
        ru_score = sum(len(re.findall(p, text_lower)) for p in ru_patterns)

        # If lots of Cyrillic letters and Russian words
        if ru_score > uz_score * 2:
            return 'ru'
        return 'uz'

    def format_number(self, val: Any) -> str:
        """Formats numbers with spaces as thousands separator."""
        if val is None:
            return "0"
        try:
            num = float(val)
            if num.is_integer():
                return f"{int(num):,}".replace(",", " ")
            return f"{num:,.2f}".replace(",", " ")
        except (ValueError, TypeError):
            return str(val)

    def answer_question(self, query: str, forced_lang: Optional[str] = None) -> Dict[str, Any]:
        """
        Main entry point for answering natural language queries.
        """
        start_time = time.perf_counter()
        lang = forced_lang or self.detect_language(query)

        # 1. Resolve Entities & Check Out-of-Scope
        entities = self.entity_indexer.resolve_entities(query)

        # Check for immediate non-existent warnings (e.g. gold, crude oil, years outside 2022-2026)
        if entities.get('warning_non_existent'):
            warning_msg = "\n".join(f"• {w}" for w in entities['warning_non_existent'])
            if lang == 'ru':
                answer = f"⚠️ **В данных нет информации по вашему запросу:**\n{warning_msg}\n\nБаза биржи охватывает только сделки со спот-товарами с 3 января 2022 года по 30 октября 2026 года."
            else:
                answer = f"⚠️ **Berilgan ma'lumotlarda bu so'rov bo'yicha javob yo'q:**\n{warning_msg}\n\nBirja ma'lumotlar bazasi faqat 2022-yil 3-yanvardan 2026-yil 30-oktabrgacha tuzilgan haqiqiy spot bitimlarini qamrab oladi."
            
            total_duration = round((time.perf_counter() - start_time) * 1000.0, 2)
            return {
                'answer': answer,
                'sql': "N/A (Bazada mavjud emas / Отсутствует в базе)",
                'columns': [],
                'rows': [],
                'row_count': 0,
                'execution_time_ms': total_duration,
                'success': True,
                'entities': entities,
                'is_empty_or_warning': True
            }

        # 2. Generate SQL
        sql, gen_reason = self.sql_generator.generate_sql(query, entities)

        # 3. Execute SQL on DuckDB
        db_res = self.db_engine.execute_query(sql)

        # 4. Self-correction loop if syntax error
        if not db_res['success'] and 'error' in db_res:
            # Try to fix by falling back to rule-based or prompt fix
            fix_sql = self.sql_generator._generate_rule_based(query, entities)
            db_res = self.db_engine.execute_query(fix_sql)
            if db_res['success']:
                sql = fix_sql

        # 5. Build Final Answer
        columns = db_res['columns']
        rows = db_res['rows']
        exec_ms = db_res['execution_time_ms']

        # Strict Anti-Hallucination: If 0 rows returned
        if not rows or len(rows) == 0:
            if lang == 'ru':
                ans_body = "❌ **В данных нет информации по данному запросу.**\nЗаписи, соответствующие указанным фильтрам, в реестре биржевых сделок не найдены."
                provenance = f"\n\n---\n📊 **Источник данных / Обоснование:**\n• Выполненный SQL-запрос:\n```sql\n{sql}\n```\n• Время выполнения: {exec_ms} мс\n• Найдено записей: 0"
            else:
                ans_body = "❌ **Berilgan ma'lumotlarda bu so'rov bo'yicha hech qanday natija topilmadi.**\nKo'rsatilgan mezonlarga mos keluvchi bitimlar yoki yozuvlar reyestrda mavjud emas."
                provenance = f"\n\n---\n📊 **Ma'lumot manbasi / Asos:**\n• Bajarilgan SQL so'rovi:\n```sql\n{sql}\n```\n• Bajarilish vaqti: {exec_ms} ms\n• Topilgan yozuvlar soni: 0 ta"

            return {
                'answer': ans_body + provenance,
                'sql': sql,
                'columns': columns,
                'rows': rows,
                'row_count': 0,
                'execution_time_ms': exec_ms,
                'success': True,
                'entities': entities,
                'is_empty_or_warning': True
            }

        # Format rows into natural language answer
        formatted_answer = self._synthesize_answer(query, entities, sql, columns, rows, exec_ms, lang)
        
        return {
            'answer': formatted_answer,
            'sql': sql,
            'columns': columns,
            'rows': rows,
            'row_count': len(rows),
            'execution_time_ms': exec_ms,
            'success': True,
            'entities': entities,
            'is_empty_or_warning': False
        }

    def _synthesize_answer(self, query: str, entities: Dict[str, Any], sql: str, columns: List[str], rows: List[Tuple], exec_ms: float, lang: str) -> str:
        """
        Uses LLM or smart deterministic template to compose the response with provenance.
        """
        # Try LLM synthesis for natural conversational flow
        llm_text = self._try_llm_synthesis(query, sql, columns, rows, lang)
        if llm_text:
            return llm_text

        # Deterministic formatting fallback
        return self._deterministic_format(query, sql, columns, rows, exec_ms, lang)

    def _try_llm_synthesis(self, query: str, sql: str, columns: List[str], rows: List[Tuple], lang: str) -> Optional[str]:
        # Format table data
        sample_rows = rows[:15]
        data_str = f"Ustunlar: {columns}\nNatijalar (jami {len(rows)} ta qator):\n"
        for i, r in enumerate(sample_rows, 1):
            data_str += f"{i}. {dict(zip(columns, r))}\n"

        prompt = f"""
Foydalanuvchi savoli: {query}
So'rov tili: {'O‘zbekcha' if lang == 'uz' else 'Русский'}
Bajarilgan SQL:
{sql}

SQL Natijasi:
{data_str}

Iltimos, ushbu ma'lumotlar asosida foydalanuvchiga aniq, ravon va to'liq javob yozing.
Qoidalar:
- Faqat yuqoridagi SQL natijalarida bor raqamlar va nomlarni yozing.
- Raqamlarni chiroyli guruhlab (masalan 12 500 000 so'm, 4 500 tonna) formatlang.
- Javob oxiriga quyidagi blokni qo'shing:
📊 **{'Ma\'lumot manbasi / Asos:' if lang == 'uz' else 'Источник данных / Обоснование:'}**
• SQL: `{sql}`
"""
        # Try Gemini
        if self.gemini_client:
            try:
                resp = self.gemini_client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt,
                    config={'system_instruction': SYSTEM_ANSWER_PROMPT, 'temperature': 0.1}
                )
                if resp.text:
                    return resp.text
            except Exception as e:
                pass

        # Try Groq
        if self.groq_client:
            try:
                resp = self.groq_client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_ANSWER_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1
                )
                if resp.choices[0].message.content:
                    return resp.choices[0].message.content
            except Exception as e:
                pass

        # Try OpenAI
        if self.openai_client:
            try:
                resp = self.openai_client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_ANSWER_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1
                )
                if resp.choices[0].message.content:
                    return resp.choices[0].message.content
            except Exception as e:
                pass

        return None

    def _deterministic_format(self, query: str, sql: str, columns: List[str], rows: List[Tuple], exec_ms: float, lang: str) -> str:
        """
        Clean, robust tabular and narrative formatting when LLM is offline.
        """
        is_ru = (lang == 'ru')
        lines = []

        if len(rows) == 1 and len(columns) <= 6:
            # Single record / aggregate answer
            row = rows[0]
            if is_ru:
                lines.append("📋 **Результаты по вашему запросу:**\n")
            else:
                lines.append("📋 **So'rovingiz bo'yicha ma'lumotlar:**\n")

            for col, val in zip(columns, row):
                formatted_val = self.format_number(val) if isinstance(val, (int, float)) else str(val)
                clean_col = col.replace('_', ' ').capitalize()
                lines.append(f"• **{clean_col}**: `{formatted_val}`")
        else:
            # Multiple records (Top list or grouped data)
            if is_ru:
                lines.append(f"📋 **Найдено записей:** `{len(rows)}` (показаны первые {min(len(rows), 10)}):\n")
            else:
                lines.append(f"📋 **Topilgan yozuvlar soni:** `{len(rows)}` ta (dastlabki {min(len(rows), 10)} tasi ko'rsatilgan):\n")

            for idx, row in enumerate(rows[:10], 1):
                item_details = []
                for col, val in zip(columns, row):
                    if val is not None and str(val).strip() != '':
                        fmt_val = self.format_number(val) if isinstance(val, (int, float)) else str(val)
                        item_details.append(f"{col}: {fmt_val}")
                lines.append(f"{idx}. " + " | ".join(item_details))

        # Provenance / Source block
        if is_ru:
            lines.append("\n---")
            lines.append("📊 **Источник данных / Обоснование:**")
            lines.append(f"• **SQL-запрос:**\n```sql\n{sql}\n```")
            lines.append(f"• **Время выполнения:** `{exec_ms} мс` (DuckDB columnar in-memory)")
            lines.append(f"• **Строк получено:** `{len(rows)}`")
        else:
            lines.append("\n---")
            lines.append("📊 **Ma'lumot manbasi / Asos:**")
            lines.append(f"• **SQL so'rovi:**\n```sql\n{sql}\n```")
            lines.append(f"• **Bajarilish vaqti:** `{exec_ms} ms` (DuckDB columnar in-memory)")
            lines.append(f"• **Qaytarilgan qatorlar:** `{len(rows)} ta`")

        return "\n".join(lines)

if __name__ == '__main__':
    agent = UzexAgent()
    tests = [
        "2024-yilda eng ko'p sement sotgan 3 ta kompaniya",
        "BK001 kodi qaysi brokerga tegishli?",
        "2023-yilda bekor qilingan bitimlar soni nechta?",
        "2027-yilda qancha bug'doy sotilgan?",
        "Oltin bo'yicha 2024-yilda qancha bitim tuzilgan?"
    ]
    for q in tests:
        print("\n" + "="*60)
        print("SAVOL:", q)
        res = agent.answer_question(q)
        print("JAVOB:\n", res['answer'])
