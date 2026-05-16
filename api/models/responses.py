"""API响应模型 — Pydantic v2"""

from datetime import date, datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ── 基础响应 ────────────────────────────────────────────

class BaseResponse(BaseModel):
    """基础响应"""
    code: int = 200
    message: str = "success"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class DataResponse(BaseResponse):
    """数据响应"""
    data: dict = {}


# ── 市场数据 ────────────────────────────────────────────

class IndexData(BaseModel):
    """指数数据"""
    name: str
    code: str
    current: float
    change: float
    change_pct: float
    volume: float
    amount: float


class MarketOverview(BaseModel):
    """市场概览"""
    date: str
    indices: List[IndexData]
    limit_up_count: int
    limit_down_count: int
    total_stocks: int
    up_count: int
    down_count: int
    volume: float


# ── 情绪周期 ────────────────────────────────────────────

class EmotionIndicators(BaseModel):
    """情绪指标"""
    up_down_ratio: float
    explode_rate: float
    profit_effect: float
    volume_change: float
    max_consecutive_boards: int
    promotion_rate: float
    break_rate: float
    dragon_premium: float
    main_inflow_ratio: float
    yingyou_activity: float
    northbound_flow: float
    theme_strength: float
    sector_linkage: float


class EmotionDiagnosis(BaseModel):
    """情绪诊断"""
    current_cycle: str
    confidence: float
    position_limit: int
    adapted_mode: str
    core_principle: str
    next_day_prediction: str
    indicators: EmotionIndicators
    history: Optional[List[dict]] = None


# ── 评分决策 ────────────────────────────────────────────

class DimensionScore(BaseModel):
    """维度评分"""
    dimension: str
    weight: int
    score: float
    details: Optional[Dict] = None


class ComprehensiveScore(BaseModel):
    """综合评分"""
    ticker: str
    name: str
    total_score: float
    rating: str
    risk_reward_ratio: float
    risk_level: str
    priority: int
    position_pct: float
    decision: str
    dimension_scores: List[DimensionScore]


class TradePlanResponse(BaseModel):
    """交易计划"""
    ticker: str
    name: str
    entry_price: float
    entry_type: str
    stop_loss: float
    take_profit: float
    position_pct: float
    risk_reward: str
    hold_conditions: List[str]
    sell_conditions: List[str]


# ── 游资 ────────────────────────────────────────────────

class YingYouMatch(BaseModel):
    """游资匹配"""
    yingyou_name: str
    ticker: str
    name: str
    match_score: float
    recommendation: str
    operation: str
    position: str
    stop_loss: str
    take_profit: str


# ── 战法 ────────────────────────────────────────────────

class TacticMatch(BaseModel):
    """战法匹配"""
    tactic_name: str
    ticker: str
    name: str
    match_score: float
    shape_verdict: str
    adaptability: str
    sustainability: str
    prediction: str


# ── 交割单 ──────────────────────────────────────────────

class TraderProfileResponse(BaseModel):
    """交易画像"""
    total_trades: int
    win_rate: float
    profit_loss_ratio: float
    max_drawdown: float
    style: str
    golden_hour: str
    strength_themes: List[str]
    weakness_themes: List[str]
    strength_modes: List[str]
    weakness_modes: List[str]
    error_patterns: List[str]


# ── 盘中监控 ────────────────────────────────────────────

class AnchorStock(BaseModel):
    """锚定标的"""
    ticker: str
    name: str
    anchor_type: str
    score: float
    expectation: str
    boards: int
    current_price: float
    change_pct: float


class FundFlowData(BaseModel):
    """资金流向"""
    sector: str
    inflow: float
    outflow: float
    net: float
    limit_up_count: int


class SectorAlert(BaseModel):
    """板块预警"""
    sector: str
    alert_type: str
    trigger: str
    urgency: str
    affected_stocks: List[str]


# ── 个股 ────────────────────────────────────────────────

class StockDetailResponse(BaseModel):
    """个股详情"""
    ticker: str
    name: str
    current_price: float
    change_pct: float
    emotion_cycle: str
    theme_position: str
    anchor_position: str
    comprehensive_score: float
    rating: str
    yingyou_matches: List[YingYouMatch]
    tactic_matches: List[TacticMatch]
    trade_plan: Optional[TradePlanResponse] = None
    risk_points: List[str]
    success_logic: List[str]
    kline: Optional[List[dict]] = None
