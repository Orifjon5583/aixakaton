"""
Pydantic Schemas and Query Plan Models for UZEX AI Analyst.
Adheres strictly to the Technical Specification (TZ).
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

# -------------------------------------------------------------
# 1. Structured Query Plan (Gemini outputs this, Backend validates)
# -------------------------------------------------------------

class FilterCondition(BaseModel):
    years: Optional[List[int]] = Field(default=None, description="Filtr qilinadigan yillar ro'yxati (2022-2026)")
    date_start: Optional[str] = Field(default=None, description="Boshlang'ich sana YYYY-MM-DD")
    date_end: Optional[str] = Field(default=None, description="Tugash sanasi YYYY-MM-DD")
    company_name: Optional[str] = Field(default=None, description="Kompaniya nomi (qisman yoki to'liq)")
    company_inn: Optional[int] = Field(default=None, description="Kompaniya STIR/INN (9 raqam)")
    company_role: Optional[Literal['seller', 'buyer', 'any']] = Field(default='any', description="Kompaniya roli")
    broker_code: Optional[str] = Field(default=None, description="Broker kodi (BK001..BK120)")
    product_name: Optional[str] = Field(default=None, description="Tovar nomi yoki kalit so'zi (sement, bug'doy, paxta va h.k.)")
    product_category: Optional[str] = Field(default=None, description="Tovar kategoriyasi")
    region: Optional[str] = Field(default=None, description="Ombor hududi (14 ta rasmiy hudud)")
    deal_status: Optional[str] = Field(default=None, description="Bitim holati: 'Исполнен', 'Аннулирован(Не оплачен)', va h.k.")
    contract_type: Optional[Literal['Внутренний', 'Экспортный']] = Field(default=None, description="Shartnoma turi")

class QueryPlan(BaseModel):
    query_type: Literal[
        'COUNT_DEALS', 
        'SUM_AMOUNT', 
        'SUM_VOLUME', 
        'AVG_PRICE', 
        'TOP_COMPANIES', 
        'TOP_PRODUCTS', 
        'COMPARE_YEARS', 
        'COMPANY_PROFILE',
        'BROKER_PROFILE',
        'GENERAL_STATS',
        'DEFAULT_RISK_ANALYSIS',
        'SPREAD_VOLATILITY_ANALYSIS',
        'AGRI_SEASONALITY_ANALYSIS',
        'EXPORT_COMMODITY_AUDIT',
        'SELLER_TURNOVER_MEDIAN',
        'OUT_OF_SCOPE'
    ] = Field(description="So'rov maqsadi va turi")
    
    target_metric: Optional[Literal[
        'deal_amount_uzs', 
        'volume_units', 
        'unit_price', 
        'deals_count'
    ]] = Field(default=None, description="Asosiy hisoblanadigan ko'rsatkich")
    
    group_by: Optional[List[str]] = Field(default=None, description="Guruhlanadigan ustunlar ro'yxati")
    filters: FilterCondition = Field(default_factory=FilterCondition, description="Qo'llaniladigan filtrlar")
    order_direction: Literal['ASC', 'DESC'] = Field(default='DESC', description="Tartiblash yo'nalishi")
    limit: int = Field(default=10, description="Natijalar soni limiti (max 100)")
    
    is_out_of_scope: bool = Field(default=False, description="Bazada mavjud bo'lmagan tovar/yil/ob'ekt so'ralganmi")
    out_of_scope_reason: Optional[str] = Field(default=None, description="Bazada nima uchun yo'qligi sababi")
    reasoning: Optional[str] = Field(default=None, description="Query-plan tanlash mantiqi")

# -------------------------------------------------------------
# 2. Chat API Request & Response
# -------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Foydalanuvchi savoli (UZ yoki RU)")
    lang: Optional[Literal['uz', 'ru']] = Field(default=None, description="Majburiy til tanlovi")

class ProvenanceData(BaseModel):
    question: str
    detected_lang: str
    dataset_version: str
    query_plan: Optional[Dict[str, Any]] = None
    executed_sql: Optional[str] = None
    execution_time_ms: float
    filters_applied: Dict[str, Any]
    row_count: int
    data_source: str = "UZEX Spot Deals Dataset (2022-2026)"

class DataTable(BaseModel):
    columns: List[str]
    rows: List[List[Any]]

class ChatResponse(BaseModel):
    answer: str
    provenance: ProvenanceData
    data_table: Optional[DataTable] = None
    status: Literal['success', 'no_data', 'out_of_scope', 'error']
    is_demo: bool = False

# -------------------------------------------------------------
# 3. Dataset Status & Admin Upload
# -------------------------------------------------------------

class ColumnMetadata(BaseModel):
    name: str
    detected_type: str
    semantic_role: Optional[str] = None
    null_count: int = 0
    unique_count: int = 0
    sample_values: List[Any] = []

class DatasetStatusResponse(BaseModel):
    loaded: bool
    is_demo: bool
    total_deals: int
    total_contracts: int
    total_participants: int
    total_brokers: int
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    dataset_name: str
    columns: List[ColumnMetadata] = []

class SchemaConfirmRequest(BaseModel):
    column_mappings: Dict[str, str] = Field(..., description="Foydalanuvchi tasdiqlagan ustunlar mappingi")

class DatasetValidationResponse(BaseModel):
    is_valid: bool
    total_rows: int
    columns_detected: List[str]
    null_statistics: Dict[str, int]
    duplicate_count: int
    date_range: Optional[Dict[str, str]] = None
    warnings: List[str] = []

# -------------------------------------------------------------
# 4. Analytics Endpoints Schemas
# -------------------------------------------------------------

class AnalyticsOverview(BaseModel):
    total_deals: int
    total_turnover_uzs: float
    total_turnover_trln: float
    total_volume_units: float
    total_participants: int
    total_brokers: int
    period: str
    is_demo: bool = False
    sellers_count: Optional[int] = None
    buyers_count: Optional[int] = None
    export_amount_uzs: Optional[float] = None
    export_amount_trln: Optional[float] = None

class YearlyStatItem(BaseModel):
    deal_year: int
    deals_count: int
    amount_uzs: float
    amount_trln: float
    volume_units: float

class TopCompanyItem(BaseModel):
    inn: int
    name: str
    region: str
    role: str
    deals_count: int
    total_amount_uzs: float

class TopProductItem(BaseModel):
    product_name: str
    deals_count: int
    total_volume: float
    unit: str
    total_amount_uzs: float
