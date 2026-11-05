"""
DuckDB Database Engine for UZEX Birja Bitimlari.
Safely executes read-only SQL queries and returns structured results with timing.
"""

import os
import time
import duckdb
from typing import Dict, List, Any, Tuple, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db', 'uzex.duckdb')

TABLE_SCHEMA_INFO = """
DATABASE SCHEMA:

1. deals (500,000 transactions, 2022-01-03 to 2026-10-30):
   - deal_id (BIGINT, PRIMARY KEY) - Номер сделки
   - deal_date (DATE) - Дата сделки (YYYY-MM-DD)
   - deal_year (INT) - Год сделки (2022..2026)
   - deal_month (INT) - Месяц сделки (1..12)
   - deal_time (VARCHAR) - Время сделки (HH:MM:SS)
   - auction_type (VARCHAR) - 'Английский аукцион', 'Обратный аукцион', 'Двусторонний аукцион'
   - quantity (DOUBLE) - Количество купленных лотов
   - lot_size (DOUBLE) - Лот (сколько единиц в одном лоте)
   - volume_units (DOUBLE) - Общий объем = quantity * lot_size
   - unit (VARCHAR) - Единица измерения ('тонна', 'килограмм', 'литр', 'штука', 'куб.метр', 'кв.метр', 'метр')
   - deal_amount_raw (DOUBLE) - Сумма сделки в валюте контракта
   - currency (VARCHAR) - 'UZS' (сум) или 'USD' (доллар)
   - usd_rate (DOUBLE) - Курс доллара на дату сделки
   - deal_amount_uzs (DOUBLE) - Сумма сделки в сумах (для USD пересчитана по курсу)
   - unit_price (DOUBLE) - Цена за единицу измерения = deal_amount_raw / volume_units
   - starting_price (DOUBLE) - Стартовая цена за единицу измерения
   - contract_id (BIGINT) - Номер контракта
   - product_name (VARCHAR) - Наименование товара со всеми атрибутами
   - region (VARCHAR) - Регион склада продавца (всего 14 регионов, например 'Toshkent shahri')
   - contract_type (VARCHAR) - 'Внутренний' (UZS) или 'Экспортный' (USD)
   - contract_form (VARCHAR) - 'Спот', 'Форвард', 'Фьючерс'
   - deal_status (VARCHAR) - 'Исполнен', 'Аннулирован(Не оплачен)', 'Исполнен(Частично)', 'Оплачен', 'Заключен', 'Ждёт оплату', 'Новый', 'Не подписан'
   - seller_inn (BIGINT) - ИНН продавца (9 цифр)
   - buyer_inn (BIGINT) - ИНН покупателя (9 цифр)
   - seller_broker (VARCHAR) - Код брокера продавца (например 'BK001')
   - buyer_broker (VARCHAR) - Код брокера покупателя (например 'BK060')
   - payment_date (DATE) - Дата оплаты (null если не оплачено)
   - delivery_date (DATE) - Дата поставки (null если не поставлено)
   - delivered_lots (DOUBLE) - Сколько лотов фактически поставлено

2. participants (14,392 companies):
   - inn (BIGINT, PRIMARY KEY) - 9-значный ИНН
   - name (VARCHAR) - Наименование компании
   - region (VARCHAR) - Регион регистрации
   - activity_type (VARCHAR) - Вид деятельности ('Торговая компания', 'Производитель', и т.д.)
   - role (VARCHAR) - 'Продавец' или 'Покупатель'
   - vat_payer (VARCHAR) - 'Да' или 'Нет'

3. brokers (120 broker offices):
   - broker_code (VARCHAR, PRIMARY KEY) - Код брокера ('BK001' .. 'BK120')
   - name (VARCHAR) - Наименование брокерской конторы
   - inn (BIGINT) - ИНН брокера
   - region (VARCHAR) - Регион

4. contracts (6,616 contracts):
   - contract_id (BIGINT, PRIMARY KEY)
   - product_name (VARCHAR) - Базовое наименование продукта
   - brand, size, sort, type, class (VARCHAR) - Атрибуты товара
   - tnved_code (VARCHAR) - Код ТН ВЭД
   - product_group (VARCHAR) - 'Высоколиквидные товары', 'Прочие товары'
   - product_category (VARCHAR) - 'Строительные материалы', 'Сельскохозяйственная продукция', 'Нефтепродукты', 'Металлопродукция', 'Химическая продукция', 'Продовольственные товары', 'Полимерная продукция', 'Промышленные товары'
   - industry (VARCHAR) - Отрасль промышленности
   - unit (VARCHAR), lot_size (DOUBLE), currency (VARCHAR), base_price (DOUBLE)
   - delivery_basis, packaging, region, warehouse_address
   - payment_term_days, delivery_term_days
   - seller_inn, reg_date, valid_until

5. usd_rates (1,765 days, 2022-01-01 to 2026-10-31):
   - rate_date (DATE, PRIMARY KEY)
   - rate (DOUBLE) - курс сум за 1 USD

6. View v_deal_details:
   Pre-joined view connecting deals with participants (seller_name, buyer_name) and brokers (seller_broker_name, buyer_broker_name).
"""

class DatabaseEngine:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._con = None

    def get_connection(self):
        if self._con is None:
            self._con = duckdb.connect(self.db_path, read_only=True)
        return self._con

    def execute_query(self, sql: str, max_rows: int = 100) -> Dict[str, Any]:
        """
        Executes a SELECT SQL query safely and measures execution time.
        """
        # Safety checks
        clean_sql = sql.strip().rstrip(';')
        first_word = clean_sql.split()[0].upper() if clean_sql else ""
        if first_word not in ['SELECT', 'WITH']:
            return {
                'success': False,
                'error': f"Only SELECT queries are allowed (found '{first_word}').",
                'columns': [],
                'rows': [],
                'row_count': 0,
                'execution_time_ms': 0.0,
                'sql': sql
            }

        forbidden_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'ATTACH', 'COPY', 'EXEC', 'INSTALL']
        for kw in forbidden_keywords:
            if re_keyword := duckdb_has_keyword(clean_sql, kw):
                return {
                    'success': False,
                    'error': f"Forbidden SQL keyword: {kw}",
                    'columns': [],
                    'rows': [],
                    'row_count': 0,
                    'execution_time_ms': 0.0,
                    'sql': sql
                }

        start = time.perf_counter()
        try:
            con = self.get_connection()
            rel = con.execute(clean_sql)
            columns = [col[0] for col in rel.description] if rel.description else []
            rows = rel.fetchmany(max_rows)
            duration_ms = (time.perf_counter() - start) * 1000.0

            return {
                'success': True,
                'columns': columns,
                'rows': rows,
                'row_count': len(rows),
                'execution_time_ms': round(duration_ms, 2),
                'sql': clean_sql,
                'error': None
            }
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000.0
            return {
                'success': False,
                'error': str(e),
                'columns': [],
                'rows': [],
                'row_count': 0,
                'execution_time_ms': round(duration_ms, 2),
                'sql': clean_sql
            }

def duckdb_has_keyword(sql: str, kw: str) -> bool:
    import re
    return bool(re.search(r'\b' + re.escape(kw) + r'\b', sql, re.IGNORECASE))

if __name__ == '__main__':
    engine = DatabaseEngine()
    test_sql = "SELECT deal_year, count(*), sum(deal_amount_uzs) FROM deals GROUP BY deal_year ORDER BY deal_year"
    res = engine.execute_query(test_sql)
    print("Test SQL Result:")
    print("Success:", res['success'])
    print("Time:", res['execution_time_ms'], "ms")
    print("Columns:", res['columns'])
    print("Rows:", res['rows'])
