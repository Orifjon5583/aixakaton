"""
SQL Compiler for UZEX AI Analyst.
Compiles a validated Pydantic QueryPlan into strict, optimized DuckDB SQL.
"""

from typing import Dict, Any, List
from backend.app.models.schemas import QueryPlan

class SQLCompiler:
    def compile_plan(self, plan: QueryPlan) -> str:
        """
        Compiles validated QueryPlan into DuckDB SQL.
        All calculations are strictly performed by SQL (per TZ section 3).
        """
        where_clauses = self._build_where_clauses(plan)
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        limit_sql = f"LIMIT {min(plan.limit, 100)}"
        source_table = "v_deal_details" if (plan.filters.company_name or plan.filters.region) else "deals"

        qt = plan.query_type

        # 1. COUNT_DEALS
        if qt == 'COUNT_DEALS':
            group_cols = plan.group_by or []
            if group_cols:
                cols_str = ", ".join(group_cols)
                return f"""
                    SELECT {cols_str}, count(*) AS deals_count 
                    FROM {source_table} 
                    {where_sql} 
                    GROUP BY {cols_str} 
                    ORDER BY deals_count {plan.order_direction} 
                    {limit_sql}
                """.strip()
            return f"SELECT count(*) AS deals_count FROM {source_table} {where_sql}".strip()

        # 2. SUM_AMOUNT
        if qt == 'SUM_AMOUNT':
            group_cols = plan.group_by or []
            if group_cols:
                cols_str = ", ".join(group_cols)
                return f"""
                    SELECT {cols_str}, coalesce(sum(deal_amount_uzs), 0) AS total_amount_uzs, count(*) AS deals_count
                    FROM {source_table} 
                    {where_sql} 
                    GROUP BY {cols_str} 
                    ORDER BY total_amount_uzs {plan.order_direction} 
                    {limit_sql}
                """.strip()
            return f"SELECT coalesce(sum(deal_amount_uzs), 0) AS total_amount_uzs, count(*) AS deals_count FROM {source_table} {where_sql}".strip()

        # 3. SUM_VOLUME
        if qt == 'SUM_VOLUME':
            return f"""
                SELECT unit, coalesce(sum(volume_units), 0) AS total_volume, count(*) AS deals_count, coalesce(sum(deal_amount_uzs), 0) AS total_amount_uzs
                FROM deals 
                {where_sql} 
                GROUP BY unit 
                ORDER BY total_volume {plan.order_direction} 
                {limit_sql}
            """.strip()

        # 4. AVG_PRICE
        if qt == 'AVG_PRICE':
            return f"""
                SELECT unit, coalesce(avg(unit_price), 0) AS avg_unit_price, count(*) AS deals_count, coalesce(sum(volume_units), 0) AS total_volume
                FROM deals 
                {where_sql} 
                GROUP BY unit 
                ORDER BY total_volume DESC 
                {limit_sql}
            """.strip()

        # 5. TOP_COMPANIES
        if qt == 'TOP_COMPANIES':
            role = plan.filters.company_role or 'seller'
            order_col = 'deals_count'
            if plan.target_metric == 'deal_amount_uzs':
                order_col = 'total_amount_uzs'
            elif plan.target_metric == 'volume_units':
                order_col = 'total_volume'

            if role == 'buyer':
                return f"""
                    SELECT buyer_name AS company_name, buyer_inn AS company_inn, buyer_region AS region,
                           count(*) AS deals_count,
                           coalesce(sum(deal_amount_uzs), 0) AS total_amount_uzs,
                           coalesce(sum(volume_units), 0) AS total_volume
                    FROM v_deal_details
                    {where_sql}
                    GROUP BY buyer_name, buyer_inn, buyer_region
                    ORDER BY {order_col} {plan.order_direction}
                    {limit_sql}
                """.strip()
            else:
                return f"""
                    SELECT seller_name AS company_name, seller_inn AS company_inn, seller_region AS region,
                           count(*) AS deals_count,
                           coalesce(sum(deal_amount_uzs), 0) AS total_amount_uzs,
                           coalesce(sum(volume_units), 0) AS total_volume
                    FROM v_deal_details
                    {where_sql}
                    GROUP BY seller_name, seller_inn, seller_region
                    ORDER BY {order_col} {plan.order_direction}
                    {limit_sql}
                """.strip()

        # 6. TOP_PRODUCTS
        if qt == 'TOP_PRODUCTS':
            return f"""
                SELECT product_name, count(*) AS deals_count,
                       coalesce(sum(volume_units), 0) AS total_volume, unit,
                       coalesce(sum(deal_amount_uzs), 0) AS total_amount_uzs
                FROM deals
                {where_sql}
                GROUP BY product_name, unit
                ORDER BY deals_count {plan.order_direction}
                {limit_sql}
            """.strip()

        # 7. COMPARE_YEARS
        if qt == 'COMPARE_YEARS':
            return f"""
                SELECT deal_year, count(*) AS deals_count,
                       coalesce(sum(deal_amount_uzs), 0) AS total_amount_uzs,
                       coalesce(sum(volume_units), 0) AS total_volume
                FROM deals
                {where_sql}
                GROUP BY deal_year
                ORDER BY deal_year ASC
            """.strip()

        # 8. BROKER_PROFILE
        if qt == 'BROKER_PROFILE':
            b_code = plan.filters.broker_code or 'BK001'
            return f"""
                SELECT b.broker_code, b.name, b.inn, b.region,
                       (SELECT count(*) FROM deals WHERE seller_broker = b.broker_code) AS deals_as_seller_broker,
                       (SELECT count(*) FROM deals WHERE buyer_broker = b.broker_code) AS deals_as_buyer_broker,
                       (SELECT coalesce(sum(deal_amount_uzs), 0) FROM deals WHERE seller_broker = b.broker_code OR buyer_broker = b.broker_code) AS total_turnover_uzs
                FROM brokers b
                WHERE b.broker_code = '{b_code}'
            """.strip()

        # 9. COMPANY_PROFILE
        if qt == 'COMPANY_PROFILE':
            inn = plan.filters.company_inn or 0
            name = plan.filters.company_name or ''
            cond = f"p.inn = {inn}" if inn else f"p.name ILIKE '%{name}%'"
            return f"""
                SELECT p.inn, p.name, p.region, p.role, p.activity_type, p.vat_payer,
                       (SELECT count(*) FROM deals WHERE seller_inn = p.inn) AS deals_as_seller,
                       (SELECT count(*) FROM deals WHERE buyer_inn = p.inn) AS deals_as_buyer,
                       (SELECT coalesce(sum(deal_amount_uzs), 0) FROM deals WHERE seller_inn = p.inn) AS total_sold_uzs,
                       (SELECT coalesce(sum(deal_amount_uzs), 0) FROM deals WHERE buyer_inn = p.inn) AS total_bought_uzs
                FROM participants p
                WHERE {cond}
                LIMIT 1
            """.strip()

        # 10. DEFAULT_RISK_ANALYSIS (Kliring, Defolt, Majburiyatlar bajarilmagani)
        if qt == 'DEFAULT_RISK_ANALYSIS':
            return f"""
                SELECT 
                    deal_status,
                    count(*) AS deals_count,
                    round(count(*) * 100.0 / (SELECT count(*) FROM deals), 2) AS percentage,
                    round(sum(deal_amount_uzs), 2) AS total_amount_uzs
                FROM deals
                GROUP BY deal_status
                ORDER BY deals_count DESC
            """.strip()

        # 11. SPREAD_VOLATILITY_ANALYSIS (Monopol tovarlar, Spred, Boshlang'ich va yakuniy narx)
        if qt == 'SPREAD_VOLATILITY_ANALYSIS':
            return f"""
                SELECT 
                    deal_year,
                    count(*) AS deals_count,
                    round(avg((unit_price - starting_price) / nullif(starting_price, 0) * 100), 2) AS avg_spread_pct,
                    round(avg(starting_price), 2) AS avg_starting_price,
                    round(avg(unit_price), 2) AS avg_deal_price,
                    round(sum(deal_amount_uzs), 2) AS total_amount_uzs
                FROM deals
                WHERE (product_name ILIKE '%бензин%' OR product_name ILIKE '%цемент%')
                GROUP BY deal_year
                ORDER BY deal_year ASC
            """.strip()

        # 12. AGRI_SEASONALITY_ANALYSIS (Bug'doy, un, paxta yog'i/shroti, Korrelyatsiya, Hosil davri)
        if qt == 'AGRI_SEASONALITY_ANALYSIS':
            return f"""
                SELECT 
                    deal_year,
                    count(*) AS deals_count,
                    round(sum(volume_units), 2) AS total_volume_tons,
                    round(avg(unit_price), 2) AS avg_unit_price,
                    round(sum(deal_amount_uzs), 2) AS total_amount_uzs
                FROM deals
                WHERE (product_name ILIKE '%пшеница%' OR product_name ILIKE '%мука%' OR product_name ILIKE '%масло%' OR product_name ILIKE '%шрот%')
                GROUP BY deal_year
                ORDER BY deal_year ASC
            """.strip()

        # Default / GENERAL_STATS
        return f"""
            SELECT deal_year, count(*) AS total_deals,
                   coalesce(sum(volume_units), 0) AS total_volume,
                   coalesce(sum(deal_amount_uzs), 0) AS total_amount_uzs
            FROM deals
            {where_sql}
            GROUP BY deal_year
            ORDER BY deal_year ASC
        """.strip()

    def _build_where_clauses(self, plan: QueryPlan) -> List[str]:
        clauses = []
        f = plan.filters

        # Years
        if f.years:
            if len(f.years) == 1:
                clauses.append(f"deal_year = {f.years[0]}")
            elif len(f.years) > 1 and sorted(f.years) == list(range(min(f.years), max(f.years) + 1)):
                clauses.append(f"deal_year BETWEEN {min(f.years)} AND {max(f.years)}")
            else:
                y_str = ", ".join(str(y) for y in f.years)
                clauses.append(f"deal_year IN ({y_str})")

        # Date range
        if f.date_start:
            clauses.append(f"deal_date >= '{f.date_start}'")
        if f.date_end:
            clauses.append(f"deal_date <= '{f.date_end}'")

        # Product name / Synonyms
        if f.product_name:
            # Match Russian database values
            clauses.append(f"product_name ILIKE '%{f.product_name}%'")

        # Region
        if f.region:
            if plan.query_type in ['TOP_PRODUCTS', 'AVG_PRICE', 'SUM_VOLUME']:
                clauses.append(f"region = '{f.region}'")
            else:
                clauses.append(f"(region = '{f.region}' OR seller_region = '{f.region}' OR buyer_region = '{f.region}')")

        # Company Name
        if f.company_name:
            clauses.append(f"(seller_name ILIKE '%{f.company_name}%' OR buyer_name ILIKE '%{f.company_name}%')")

        # Status
        if f.deal_status:
            clauses.append(f"deal_status = '{f.deal_status}'")

        # Contract Type (Внутренний / Экспортный)
        if f.contract_type:
            clauses.append(f"contract_type = '{f.contract_type}'")

        # Company INN
        if f.company_inn:
            if f.company_role == 'seller':
                clauses.append(f"seller_inn = {f.company_inn}")
            elif f.company_role == 'buyer':
                clauses.append(f"buyer_inn = {f.company_inn}")
            else:
                clauses.append(f"(seller_inn = {f.company_inn} OR buyer_inn = {f.company_inn})")

        # Broker Code
        if f.broker_code:
            clauses.append(f"(seller_broker = '{f.broker_code}' OR buyer_broker = '{f.broker_code}')")

        return clauses

sql_compiler = SQLCompiler()
