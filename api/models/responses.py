"""API 响应模型定义 — 短线致胜 AI 交易智能体"""

from pydantic import BaseModel
from typing import Any, Optional, List, Dict

# ------------------------------
# 基础响应模型（通用返回结构）
# ------------------------------
class BaseResponse(BaseModel):
    code: int = 200
    message: str = "success"

class ApiResponse(BaseResponse):
    data: Optional[Any] = None

class DataResponse(BaseResponse):
    data: Optional[Dict[str, Any]] = None

# ------------------------------
# 市场模块响应模型
# ------------------------------
class IndexData(BaseModel):
    code: str
    name: str
    current: float = 0.0
    price: float = 0.0
    change: float = 0.0
    change_pct: float = 0.0
    volume: float = 0.0
    amount: float = 0.0

class MarketOverview(BaseModel):
    date: str
    indices: List[IndexData] = []
    limit_up_count: int = 0
    limit_down_count: int = 0
    total_stocks: int = 0
    up_count: int = 0
    down_count: int = 0
    volume: float = 0.0
    total_market_cap: float = 0.0
    rise_count: int = 0
    fall_count: int = 0
    flat_count: int = 0
    top_indexes: List[IndexData] = []

# ------------------------------
# 情绪分析模块响应模型
# ------------------------------
class EmotionIndicators(BaseModel):
    fear_index: float = 0.0
    greed_index: float = 0.0
    sentiment_score: float = 0.0
    market_volatility: float = 0.0
    up_down_ratio: float = 0.0
    explode_rate: float = 0.0
    profit_effect: float = 0.0
    volume_change: float = 0.0
    max_consecutive_boards: int = 0
    promotion_rate: float = 0.0
    break_rate: float = 0.0
    dragon_premium: float = 0.0
    main_inflow_ratio: float = 0.0
    yingyou_activity: float = 0.0
    northbound_flow: float = 0.0
    theme_strength: float = 0.0
    sector_linkage: float = 0.0

class EmotionDiagnosis(BaseModel):
    status: str = ""
    current_cycle: str = ""
    confidence: float = 0.0
    position_limit: int = 0
    adapted_mode: str = ""
    core_principle: str = ""
    next_day_prediction: str = ""
    indicators: Optional[EmotionIndicators] = None
    analysis: str = ""
    suggestion: str = ""

# ------------------------------
# 盘中监控模块响应模型
# ------------------------------
class AnchorStock(BaseModel):
    code: str = ""
    ticker: str = ""
    name: str = ""
    price: float = 0.0
    current_price: float = 0.0
    change_pct: float = 0.0
    turnover_rate: float = 0.0
    volume_ratio: float = 0.0
    anchor_type: str = ""
    score: float = 0.0
    expectation: str = ""
    boards: int = 0

class FundFlowData(BaseModel):
    time: str = ""
    sector: str = ""
    main_net_inflow: float = 0.0
    retail_net_inflow: float = 0.0
    institutional_net_inflow: float = 0.0
    total_net_inflow: float = 0.0
    inflow: float = 0.0
    outflow: float = 0.0
    net: float = 0.0
    limit_up_count: int = 0

class SectorAlert(BaseModel):
    sector_name: str = ""
    sector: str = ""
    lead_stock: str = ""
    lead_change_pct: float = 0.0
    sector_avg_change: float = 0.0
    hot_stocks: List[str] = []
    alert_type: str = ""
    trigger: str = ""
    urgency: str = ""
    affected_stocks: List[str] = []

# ------------------------------
# 游资匹配模块响应模型
# ------------------------------
class YingYouMatch(BaseModel):
    code: str = ""
    ticker: str = ""
    name: str = ""
    yingyou_name: str = ""
    match_score: float = 0.0
    fund_flow: float = 0.0
    price_strength: float = 0.0
    volume_ratio: float = 0.0
    recommendation: str = ""
    operation: str = ""
    position: str = ""
    stop_loss: str = ""
    take_profit: str = ""

class YingYouRank(BaseModel):
    rank: int = 0
    code: str = ""
    name: str = ""
    match_score: float = 0.0
    recent_performance: float = 0.0

# ------------------------------
# 战法匹配模块响应模型
# ------------------------------
class TacticMatch(BaseModel):
    tactic_name: str = ""
    ticker: str = ""
    name: str = ""
    stock_name: str = ""
    match_score: float = 0.0
    conditions_met: int = 0
    conditions_failed: int = 0
    shape_verdict: str = ""
    adaptability: str = ""
    sustainability: str = ""
    prediction: str = ""
    operation_guide: str = ""

# ------------------------------
# 评分决策模块响应模型
# ------------------------------
class DimensionScore(BaseModel):
    dimension: str = ""
    weight: float = 0.0
    score: float = 0.0
    details: Dict[str, Any] = {}

class ComprehensiveScore(BaseModel):
    ticker: str = ""
    name: str = ""
    total_score: float = 0.0
    rating: str = ""
    risk_reward_ratio: float = 0.0
    risk_level: str = ""
    priority: int = 0
    position_pct: float = 0.0
    decision: str = ""
    dimension_scores: List[DimensionScore] = []

class TradePlanResponse(BaseModel):
    ticker: str = ""
    name: str = ""
    entry_price: float = 0.0
    entry_type: str = ""
    stop_loss: float = 0.0
    take_profit: float = 0.0
    position_pct: float = 0.0
    risk_reward: str = ""
    hold_conditions: List[str] = []
    sell_conditions: List[str] = []

# ------------------------------
# 交易诊断模块响应模型
# ------------------------------
class TraderProfileResponse(BaseModel):
    total_trades: int = 0
    win_rate: float = 0.0
    profit_loss_ratio: float = 0.0
    max_drawdown: float = 0.0
    style: str = ""
    golden_hour: str = ""
    strength_themes: List[str] = []
    weakness_themes: List[str] = []
    strength_modes: List[str] = []
    weakness_modes: List[str] = []
    error_patterns: List[str] = []

# ------------------------------
# 交易日志模块响应模型
# ------------------------------
class TradeJournalEntry(BaseModel):
    id: int = 0
    symbol: str = ""
    action: str = ""
    price: float = 0.0
    quantity: int = 0
    timestamp: str = ""
    notes: Optional[str] = None

class JournalSummary(BaseModel):
    total_trades: int = 0
    win_rate: float = 0.0
    profit_loss: float = 0.0
    avg_holding_time: float = 0.0

# ------------------------------
# 个股详情响应模型
# ------------------------------
class StockDetailResponse(BaseModel):
    ticker: str = ""
    name: str = ""
    current_price: float = 0.0
    change_pct: float = 0.0
    emotion_cycle: str = ""
    theme_position: str = ""
    anchor_position: str = ""
    comprehensive_score: float = 0.0
    rating: str = ""
    yingyou_matches: List[YingYouMatch] = []
    tactic_matches: List[TacticMatch] = []
    trade_plan: Optional[TradePlanResponse] = None
    risk_points: List[str] = []
    success_logic: List[str] = []
    kline: List[Dict[str, Any]] = []