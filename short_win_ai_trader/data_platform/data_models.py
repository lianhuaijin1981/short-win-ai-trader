"""数据模型定义 — 短线致胜AI交易智能体核心业务数据结构"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional, Literal


# ==================== 枚举定义 ====================

class RiskLevel(str, Enum):
    """风险等级"""
    SAFE = "安全"
    CAUTIOUS = "谨慎"
    HIGH_RISK = "高风险"
    FORBIDDEN = "禁入"


class EmotionCycle(str, Enum):
    """情绪周期六段划分"""
    CHAOS = "混沌期"
    START = "启动期"
    FERMENT = "发酵期"
    PEAK = "高潮期"
    DIVERGE = "分歧期"
    RETREAT = "退潮期"


class ThemeCycle(str, Enum):
    """题材生命周期"""
    SPROUT = "题材萌芽"
    FERMENT = "资金发酵"
    ACCELERATE = "主升加速"
    DIVERGE = "高位分歧"
    COMPLEMENT = "补涨收尾"
    RETREAT = "题材退潮"


class AnchorType(str, Enum):
    """锚定标的类型"""
    TOTAL_DRAGON = "市场总龙"
    BRANCH_DRAGON = "主线分支龙头"
    PIONEER = "先锋龙"
    SECTOR_CORE = "板块中军"


class ExpectationLevel(str, Enum):
    """预期分级"""
    BELOW = "低于预期"
    MEET = "符合预期"
    ABOVE = "强于预期"


class Recommendation(str, Enum):
    """推荐等级"""
    STRONG_BUY = "强烈推荐"
    BUY = "谨慎推荐"
    WATCH = "观察关注"
    AVOID = "不建议"


class EntryType(str, Enum):
    """入场类型"""
    BREAKOUT = "突破入场"
    PULLBACK = "回踩入场"
    DIVERGENCE = "分歧入场"


# ==================== 基础行情数据模型 ====================

@dataclass
class StockPrice:
    """个股价格数据"""
    ticker: str
    name: str = ""
    trade_date: Optional[date] = None
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: int = 0
    amount: float = 0.0
    change_pct: float = 0.0
    amplitude: float = 0.0
    turnover_rate: float = 0.0
    ma5: float = 0.0
    ma10: float = 0.0
    ma20: float = 0.0


@dataclass
class MarketSnapshot:
    """市场快照"""
    trade_date: Optional[date] = None
    total_stocks: int = 0
    up_count: int = 0
    down_count: int = 0
    limit_up_count: int = 0
    limit_down_count: int = 0
    explode_rate: float = 0.0
    total_volume: float = 0.0
    volume_change_pct: float = 0.0
    sh_index: float = 0.0
    sz_index: float = 0.0
    cy_index: float = 0.0


@dataclass
class LimitUpStock:
    """涨停股数据"""
    ticker: str = ""
    name: str = ""
    consecutive_boards: int = 0
    theme: str = ""
    first_limit_up_time: Optional[str] = None
    explode_count: int = 0
    seal_amount: float = 0.0
    change_pct: float = 0.0
    volume_ratio: float = 0.0


@dataclass
class ThemeData:
    """题材数据"""
    theme_name: str = ""
    stocks: List[str] = field(default_factory=list)
    avg_change_pct: float = 0.0
    total_inflow: float = 0.0
    limit_up_count: int = 0
    leading_stock: Optional[str] = None
    cycle_stage: Optional[ThemeCycle] = None
    description: str = ""


@dataclass
class DragonBond:
    """龙虎榜数据"""
    ticker: str = ""
    trade_date: Optional[date] = None
    seat_name: str = ""
    buy_amount: float = 0.0
    sell_amount: float = 0.0
    net_amount: float = 0.0
    seat_type: Literal["游资", "机构", "散户", "未知"] = "未知"


# ==================== 情绪周期数据模型 ====================

@dataclass
class EmotionIndicators:
    """情绪量化指标"""
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
    theme_sustainability: float = 0.0


@dataclass
class EmotionDiagnosis:
    """情绪周期诊断结果"""
    current_cycle: EmotionCycle = EmotionCycle.CHAOS
    confidence: float = 0.0
    indicators: Optional[EmotionIndicators] = None
    position_limit: int = 0
    adapted_mode: str = ""
    core_principle: str = ""
    next_day_prediction: str = ""
    reasons: List[str] = field(default_factory=list)


@dataclass
class ThemeCycleAnalysis:
    """题材周期分析"""
    theme_name: str = ""
    current_stage: ThemeCycle = ThemeCycle.SPROUT
    persistence_type: str = ""  # 长期主线/短期套利/一日游
    prediction: str = ""
    entry_point: str = ""
    add_point: str = ""
    take_profit_point: str = ""
    exit_point: str = ""
    rotation_target: Optional[str] = None


@dataclass
class NextDayPrediction:
    """次日趋势预判"""
    trend: str = ""  # 震荡整理/强势延续/弱势调整/探底修复
    support_level: float = 0.0
    resistance_level: float = 0.0
    risk_warning: Optional[str] = None


# ==================== 锚定标的数据模型 ====================

@dataclass
class AnchorStock:
    """锚定标的"""
    ticker: str = ""
    name: str = ""
    anchor_type: AnchorType = AnchorType.TOTAL_DRAGON
    score: float = 0.0
    height_weight: float = 0.0
    recognition_weight: float = 0.0
    drive_weight: float = 0.0
    premium_weight: float = 0.0
    expectation: ExpectationLevel = ExpectationLevel.MEET
    operation_advice: str = ""
    expected_open_high: float = 0.0
    expected_volume_ratio: float = 0.0


@dataclass
class DragonEcology:
    """龙头生态梯队"""
    dragon: Optional[AnchorStock] = None
    pioneer: Optional[AnchorStock] = None
    core: Optional[AnchorStock] = None
    followers: List[str] = field(default_factory=list)
    ecology_health: float = 0.0
    risk_warning: Optional[str] = None


# ==================== 资金流向数据模型 ====================

@dataclass
class FundFlowReport:
    """资金流向报告"""
    first_direction: str = ""  # 第一进攻方向
    second_direction: str = ""  # 第二进攻方向
    rotation_direction: str = ""  # 轮动套利方向
    inflow_sectors: Dict[str, float] = field(default_factory=dict)
    outflow_sectors: Dict[str, float] = field(default_factory=dict)
    outflow_type: str = ""  # 良性调仓/恐慌撤退
    summary: str = ""


@dataclass
class SectorAlert:
    """板块效应预警"""
    sector_name: str = ""
    alert_type: str = ""  # 强板块效应/批量高开/分支异动
    trigger_condition: str = ""
    affected_stocks: List[str] = field(default_factory=list)
    urgency: str = "normal"  # normal/high/critical
    advice: str = ""


@dataclass
class ExpectationEvaluation:
    """预期评估结果"""
    ticker: str = ""
    expectation: ExpectationLevel = ExpectationLevel.MEET
    actual_open: float = 0.0
    actual_high_5m: float = 0.0
    volume_status: str = ""  # 放量/缩量/正常
    support_status: str = ""  # 强承接/弱承接/无承接
    operation: str = ""


@dataclass
class SessionAlert:
    """分时段提醒"""
    session: str = ""  # 集合竞价/开盘黄金30分/盘中震荡/尾盘
    timestamp: Optional[datetime] = None
    content: str = ""
    priority: str = "normal"
    related_stocks: List[str] = field(default_factory=list)


# ==================== 游资模式数据模型 ====================

@dataclass
class YingYouFingerprint:
    """游资数字指纹"""
    name: str = ""
    philosophy: str = ""
    stock_selection_rules: Dict = field(default_factory=dict)
    entry_timing: Dict = field(default_factory=dict)
    risk_rules: Dict = field(default_factory=dict)
    classic_tactics: List[str] = field(default_factory=list)
    preferred_themes: List[str] = field(default_factory=list)
    risk_profile: str = ""  # 激进/稳健/保守


@dataclass
class YingYouMatchResult:
    """游资匹配结果"""
    yingyou_name: str = ""
    ticker: str = ""
    stock_name: str = ""
    match_score: float = 0.0
    recommendation: str = ""
    reasons: List[str] = field(default_factory=list)
    operation: str = ""
    position: str = ""
    stop_loss: str = ""
    take_profit: str = ""


@dataclass
class YingYouDiagnosisResult:
    """游资诊断结果"""
    yingyou_name: str = ""
    emotion_position: str = ""  # 当前情绪阶段操作偏好
    fund_direction_match: bool = False
    top_picks: List[YingYouMatchResult] = field(default_factory=list)


@dataclass
class ConsensusResult:
    """游资共识/分歧分析"""
    consensus_stocks: List[Dict] = field(default_factory=list)
    diverge_stocks: List[Dict] = field(default_factory=list)
    summary: str = ""


@dataclass
class PortfolioStrategy:
    """组合策略"""
    strategy_type: str = ""  # 激进/稳健/保守
    yingyou_combo: List[str] = field(default_factory=list)
    adapted_cycle: List[str] = field(default_factory=list)
    description: str = ""


# ==================== 战法数据模型 ====================

@dataclass
class TacticRule:
    """战法规则"""
    name: str = ""
    core_logic: str = ""
    hard_conditions: Dict = field(default_factory=dict)
    best_env: Dict = field(default_factory=dict)
    entry_zone: str = ""
    risk_boundary: Dict = field(default_factory=dict)
    applicable_cycles: List[str] = field(default_factory=list)


@dataclass
class TacticMatchResult:
    """战法匹配结果"""
    tactic_name: str = ""
    ticker: str = ""
    stock_name: str = ""
    conditions_met: List[str] = field(default_factory=list)
    conditions_failed: List[str] = field(default_factory=list)
    shape_verdict: str = ""
    adaptability: str = ""
    sustainability: str = ""
    prediction: str = ""
    operation_guide: str = ""
    match_score: float = 0.0


@dataclass
class ResonanceStock:
    """战法共振股"""
    ticker: str = ""
    name: str = ""
    matched_tactics: List[str] = field(default_factory=list)
    resonance_level: str = ""  # 双战法/三战法/多战法
    priority: int = 0


@dataclass
class TacticSuitability:
    """战法适用性"""
    suitable_tactics: List[str] = field(default_factory=list)
    forbidden_tactics: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# ==================== 综合评分数据模型 ====================

@dataclass
class DimensionScore:
    """维度评分"""
    dimension: str = ""
    weight: float = 0.0
    score: float = 0.0
    details: Dict = field(default_factory=dict)


@dataclass
class ComprehensiveScore:
    """综合评分结果"""
    ticker: str = ""
    stock_name: str = ""
    total_score: float = 0.0
    rating: str = ""  # 顶级/优质/良好/一般/劣质
    dimension_scores: List[DimensionScore] = field(default_factory=list)
    risk_reward_ratio: float = 0.0
    risk_level: RiskLevel = RiskLevel.SAFE
    priority: int = 0
    decision: str = ""


@dataclass
class TradePlan:
    """完整交易计划"""
    ticker: str = ""
    stock_name: str = ""
    entry_price: float = 0.0
    entry_type: str = ""
    stop_loss_price: float = 0.0
    take_profit_price: float = 0.0
    position_pct: float = 0.0
    hold_conditions: List[str] = field(default_factory=list)
    sell_conditions: List[str] = field(default_factory=list)
    emergency_plan: str = ""


# ==================== 交割单数据模型 ====================

@dataclass
class TradeRecord:
    """交易记录"""
    trade_id: str = ""
    ticker: str = ""
    stock_name: str = ""
    trade_date: Optional[datetime] = None
    trade_type: str = ""  # 买入/卖出
    price: float = 0.0
    volume: int = 0
    amount: float = 0.0
    trade_mode: str = ""  # 打板/低吸/半路/潜伏/接力/套利
    profit_loss: Optional[float] = None
    profit_loss_pct: Optional[float] = None


@dataclass
class SingleTradeDiagnosis:
    """单笔交易诊断"""
    trade: Optional[TradeRecord] = None
    is_profitable: bool = False
    success_factors: List[str] = field(default_factory=list)
    failure_reasons: List[str] = field(default_factory=list)
    error_type: Optional[str] = None
    improvement: str = ""


@dataclass
class TraderProfile:
    """交易者画像"""
    total_trades: int = 0
    win_rate: float = 0.0
    profit_loss_ratio: float = 0.0
    max_drawdown: float = 0.0
    avg_profit: float = 0.0
    avg_loss: float = 0.0
    style: str = ""  # 龙头接力/分歧低吸/事件催化/趋势波段/冰点试错/首板挖掘
    golden_hour: str = ""  # 黄金出手时段
    strength_themes: List[str] = field(default_factory=list)
    weakness_themes: List[str] = field(default_factory=list)
    strength_modes: List[str] = field(default_factory=list)
    weakness_modes: List[str] = field(default_factory=list)
    error_patterns: List[str] = field(default_factory=list)


@dataclass
class CustomStockAnalysis:
    """自定义标的全维度研判"""
    ticker: str = ""
    name: str = ""
    comprehensive_score: float = 0.0
    rating: str = ""
    emotion_cycle: str = ""
    theme_position: str = ""
    anchor_position: str = ""
    yingyou_matches: List[Dict] = field(default_factory=list)
    tactic_matches: List[Dict] = field(default_factory=list)
    success_logic: List[str] = field(default_factory=list)
    risk_points: List[str] = field(default_factory=list)
    trade_plan: Optional[TradePlan] = None
    style_advice: str = ""


# ==================== 统一报告数据模型 ====================

@dataclass
class PreMarketReport:
    """盘前报告"""
    date: Optional[date] = None
    news_summary: str = ""
    scored_news: List[Dict] = field(default_factory=list)
    risk_list: List[str] = field(default_factory=list)
    theme_priorities: List[str] = field(default_factory=list)
    emotion_forecast: str = ""


@dataclass
class IntradayReport:
    """盘中报告"""
    timestamp: Optional[datetime] = None
    anchors: List[AnchorStock] = field(default_factory=list)
    fund_flow: Optional[FundFlowReport] = None
    sector_alerts: List[SectorAlert] = field(default_factory=list)
    expectations: List[ExpectationEvaluation] = field(default_factory=list)
    dragon_ecology: Optional[DragonEcology] = None


@dataclass
class PostMarketReport:
    """盘后报告"""
    date: Optional[date] = None
    market_replay: str = ""
    emotion_diagnosis: Optional[EmotionDiagnosis] = None
    theme_analysis: List[ThemeCycleAnalysis] = field(default_factory=list)
    next_day_prediction: Optional[NextDayPrediction] = None
    yingyou_recommendations: List[YingYouMatchResult] = field(default_factory=list)
    tactic_screening: List[TacticMatchResult] = field(default_factory=list)
    scoring_results: List[ComprehensiveScore] = field(default_factory=list)
    trade_plans: List[TradePlan] = field(default_factory=list)


@dataclass
class StockAnalysisReport:
    """个股全维度分析报告"""
    ticker: str = ""
    name: str = ""
    price: float = 0.0
    change_pct: float = 0.0
    emotion_context: str = ""
    yingyou_matches: List[YingYouMatchResult] = field(default_factory=list)
    tactic_matches: List[TacticMatchResult] = field(default_factory=list)
    comprehensive_score: Optional[ComprehensiveScore] = None
    trade_plan: Optional[TradePlan] = None
    risk_warnings: List[str] = field(default_factory=list)
