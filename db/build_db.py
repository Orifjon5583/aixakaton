"""
Build and optimize the DuckDB database for UZEX AI Hackathon 2026.
Loads and processes 500,000 deals, 6,616 contracts, 14,392 participants, 120 brokers, and 1,765 USD exchange rates.
"""

import os
import sys
import io
import glob
import time
import duckdb
import pandas as pd

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'uzex_spot_data')
DB_PATH = os.path.join(os.path.dirname(__file__), 'uzex.duckdb')

def build_database():
    start_time = time.time()
    print(f"Connecting to DuckDB at {DB_PATH}...")
    
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print("Removed existing database.")
        except Exception as e:
            print("Notice:", e)

    con = duckdb.connect(DB_PATH)
    
    # 1. USD Rates
    print("Loading usd_rates.csv...")
    usd_csv = os.path.join(DATA_DIR, 'usd_rates.csv').replace('\\', '/')
    con.execute(f"""
        CREATE TABLE usd_rates AS
        SELECT 
            strptime("Дата"::VARCHAR, '%d.%m.%Y')::DATE AS rate_date,
            "Курс"::DOUBLE AS rate
        FROM read_csv('{usd_csv}', header=true, all_varchar=true)
    """)
    con.execute("CREATE UNIQUE INDEX idx_usd_rates_date ON usd_rates(rate_date)")
    print(f"Loaded {con.execute('SELECT count(*) FROM usd_rates').fetchone()[0]} exchange rates.")

    # 2. Brokers
    print("Loading brokers.csv...")
    brokers_csv = os.path.join(DATA_DIR, 'brokers.csv').replace('\\', '/')
    con.execute(f"""
        CREATE TABLE brokers AS
        SELECT 
            "Код брокера"::VARCHAR AS broker_code,
            "Наименование"::VARCHAR AS name,
            "ИНН"::BIGINT AS inn,
            "Регион"::VARCHAR AS region
        FROM read_csv('{brokers_csv}', header=true, all_varchar=true)
    """)
    con.execute("CREATE UNIQUE INDEX idx_brokers_code ON brokers(broker_code)")
    print(f"Loaded {con.execute('SELECT count(*) FROM brokers').fetchone()[0]} brokers.")

    # 3. Participants
    print("Loading participants.csv...")
    participants_csv = os.path.join(DATA_DIR, 'participants.csv').replace('\\', '/')
    con.execute(f"""
        CREATE TABLE participants AS
        SELECT 
            "ИНН"::BIGINT AS inn,
            "Наименование"::VARCHAR AS name,
            "Регион"::VARCHAR AS region,
            "Вид деятельности"::VARCHAR AS activity_type,
            "Роль"::VARCHAR AS role,
            "Плательщик НДС"::VARCHAR AS vat_payer
        FROM read_csv('{participants_csv}', header=true, all_varchar=true)
    """)
    con.execute("CREATE UNIQUE INDEX idx_participants_inn ON participants(inn)")
    print(f"Loaded {con.execute('SELECT count(*) FROM participants').fetchone()[0]} participants.")

    # 4. Contracts
    print("Loading contracts.csv...")
    contracts_csv = os.path.join(DATA_DIR, 'contracts.csv').replace('\\', '/')
    con.execute(f"""
        CREATE TABLE contracts AS
        SELECT 
            "Номер контракта"::BIGINT AS contract_id,
            "Наименование продукта"::VARCHAR AS product_name,
            "Марка товара"::VARCHAR AS brand,
            "Размер товара"::VARCHAR AS size,
            "Сорт товара"::VARCHAR AS sort,
            "Тип товара"::VARCHAR AS type,
            "Класс товара"::VARCHAR AS class,
            "Код ТН ВЭД"::VARCHAR AS tnved_code,
            "Группа товара"::VARCHAR AS product_group,
            "Категория товара"::VARCHAR AS product_category,
            "Отрасль промышленности"::VARCHAR AS industry,
            "Единица измерения"::VARCHAR AS unit,
            "Лот"::DOUBLE AS lot_size,
            "Валюта"::VARCHAR AS currency,
            "Базисная цена"::DOUBLE AS base_price,
            "Сумма залога"::VARCHAR AS deposit_pct,
            "Базис поставки"::VARCHAR AS delivery_basis,
            "Регион"::VARCHAR AS region,
            "Адрес склада"::VARCHAR AS warehouse_address,
            "Тип торгов"::VARCHAR AS auction_type,
            "Тип контракта"::VARCHAR AS contract_type,
            "Форма контракта"::VARCHAR AS contract_form,
            TRY_CAST("Срок оплаты" AS BIGINT) AS payment_term_days,
            TRY_CAST("Срок поставки" AS BIGINT) AS delivery_term_days,
            "Упаковка"::VARCHAR AS packaging,
            "ИНН продавца"::BIGINT AS seller_inn,
            CASE WHEN "Дата регистрации" IS NOT NULL AND trim("Дата регистрации") != '' 
                 THEN strptime(trim("Дата регистрации"), '%d.%m.%Y')::DATE ELSE NULL END AS reg_date,
            CASE WHEN "Действует до" IS NOT NULL AND trim("Действует до") != '' 
                 THEN strptime(trim("Действует до"), '%d.%m.%Y')::DATE ELSE NULL END AS valid_until
        FROM read_csv('{contracts_csv}', header=true, all_varchar=true)
    """)
    con.execute("CREATE UNIQUE INDEX idx_contracts_id ON contracts(contract_id)")
    print(f"Loaded {con.execute('SELECT count(*) FROM contracts').fetchone()[0]} contracts.")

    # 5. Deals
    print("Loading and cleaning 500,000 deals from deals_2022.csv .. deals_2026.csv...")
    deal_files = sorted(glob.glob(os.path.join(DATA_DIR, 'deals_*.csv')))
    deal_files_sql = [f.replace('\\', '/') for f in deal_files]
    files_list_str = str(deal_files_sql)

    con.execute(f"""
        CREATE TABLE deals AS
        WITH raw_deals AS (
            SELECT 
                "Номер сделки"::BIGINT AS deal_id,
                strptime("Дата сделки", '%d.%m.%Y')::DATE AS deal_date,
                "Время сделки"::VARCHAR AS deal_time,
                "Тип торгов"::VARCHAR AS auction_type,
                "Количество"::DOUBLE AS quantity,
                replace(replace("Сумма сделки", ' ', ''), chr(160), '')::DOUBLE AS deal_amount_raw,
                replace(replace("Стартовая цена", ' ', ''), chr(160), '')::DOUBLE AS starting_price,
                "Номер контракта"::BIGINT AS contract_id,
                "Наименование товара"::VARCHAR AS product_name,
                "Лот"::DOUBLE AS lot_size,
                "Единица измерения"::VARCHAR AS unit,
                "Регион"::VARCHAR AS region,
                "Тип контракта"::VARCHAR AS contract_type,
                "Форма контракта"::VARCHAR AS contract_form,
                "Состояние сделки"::VARCHAR AS deal_status,
                "ИНН продавца"::BIGINT AS seller_inn,
                "ИНН покупателя"::BIGINT AS buyer_inn,
                "Брокер продавца"::VARCHAR AS seller_broker,
                "Брокер покупателя"::VARCHAR AS buyer_broker,
                CASE WHEN "Дата оплаты" IS NOT NULL AND trim("Дата оплаты") != '' 
                     THEN strptime(trim("Дата оплаты"), '%d.%m.%Y')::DATE ELSE NULL END AS payment_date,
                CASE WHEN "Дата поставки" IS NOT NULL AND trim("Дата поставки") != '' 
                     THEN strptime(trim("Дата поставки"), '%d.%m.%Y')::DATE ELSE NULL END AS delivery_date,
                TRY_CAST("Поставлено" AS DOUBLE) AS delivered_lots
            FROM read_csv({files_list_str}, header=true, all_varchar=true)
        )
        SELECT 
            d.*,
            (d.quantity * d.lot_size) AS volume_units,
            CASE WHEN (d.quantity * d.lot_size) > 0 THEN d.deal_amount_raw / (d.quantity * d.lot_size) ELSE 0 END AS unit_price,
            CASE WHEN d.contract_type = 'Экспортный' THEN 'USD' ELSE 'UZS' END AS currency,
            coalesce(r.rate, 1.0) AS usd_rate,
            CASE 
                WHEN d.contract_type = 'Экспортный' THEN d.deal_amount_raw * coalesce(r.rate, 1.0)
                ELSE d.deal_amount_raw 
            END AS deal_amount_uzs,
            extract(year FROM d.deal_date)::INT AS deal_year,
            extract(month FROM d.deal_date)::INT AS deal_month
        FROM raw_deals d
        LEFT JOIN usd_rates r ON d.deal_date = r.rate_date
    """)
    
    total_deals = con.execute("SELECT count(*) FROM deals").fetchone()[0]
    print(f"Loaded {total_deals} deals successfully!")

    # 6. Indexes for lightning speed
    print("Creating indexes on deals...")
    con.execute("CREATE UNIQUE INDEX idx_deals_id ON deals(deal_id)")
    con.execute("CREATE INDEX idx_deals_date ON deals(deal_date)")
    con.execute("CREATE INDEX idx_deals_year ON deals(deal_year)")
    con.execute("CREATE INDEX idx_deals_contract ON deals(contract_id)")
    con.execute("CREATE INDEX idx_deals_seller ON deals(seller_inn)")
    con.execute("CREATE INDEX idx_deals_buyer ON deals(buyer_inn)")
    con.execute("CREATE INDEX idx_deals_seller_broker ON deals(seller_broker)")
    con.execute("CREATE INDEX idx_deals_buyer_broker ON deals(buyer_broker)")
    con.execute("CREATE INDEX idx_deals_status ON deals(deal_status)")
    con.execute("CREATE INDEX idx_deals_region ON deals(region)")

    # 7. Pre-computed summary views for high-frequency queries
    print("Creating helpful views...")
    con.execute("""
        CREATE VIEW v_deal_details AS
        SELECT 
            d.deal_id,
            d.deal_date,
            d.deal_year,
            d.deal_month,
            d.deal_time,
            d.auction_type,
            d.contract_id,
            d.product_name,
            d.quantity,
            d.lot_size,
            d.volume_units,
            d.unit,
            d.currency,
            d.deal_amount_raw,
            d.deal_amount_uzs,
            d.unit_price,
            d.starting_price,
            d.region,
            d.contract_type,
            d.contract_form,
            d.deal_status,
            d.seller_inn,
            sp.name AS seller_name,
            sp.region AS seller_region,
            d.buyer_inn,
            bp.name AS buyer_name,
            bp.region AS buyer_region,
            d.seller_broker,
            sb.name AS seller_broker_name,
            d.buyer_broker,
            bb.name AS buyer_broker_name,
            d.payment_date,
            d.delivery_date,
            d.delivered_lots
        FROM deals d
        LEFT JOIN participants sp ON d.seller_inn = sp.inn
        LEFT JOIN participants bp ON d.buyer_inn = bp.inn
        LEFT JOIN brokers sb ON d.seller_broker = sb.broker_code
        LEFT JOIN brokers bb ON d.buyer_broker = bb.broker_code
    """)

    # Verify counts and sample
    sample = con.execute("""
        SELECT deal_id, deal_date, product_name, currency, deal_amount_raw, deal_amount_uzs, seller_name, buyer_name
        FROM v_deal_details
        LIMIT 3
    """).fetchall()
    print("Sample deals:")
    for row in sample:
        print(row)

    elapsed = time.time() - start_time
    print(f"Database build complete in {elapsed:.2f} seconds!")
    con.close()

if __name__ == '__main__':
    build_database()
