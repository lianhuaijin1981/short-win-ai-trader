"""交易笔记数据模型

定义交易笔记模块的所有数据结构:
- PositionRecord: 持仓记录
- TradeReview: 交易复盘记录
- NextDayPlan: 次日交易计划
- WatchStock: 观察标的
- TradeNote: 完整交易笔记（当日复盘+次日计划）
- VoiceNote: 语音笔记
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Dict, List, Optional


# ── 枚举定义 ─────────────────────────────────────────────

class TradeDirection(str, Enum):
    """交易方向"""
    BUY = "买入"
    SELL = "卖出"
    HOLD = "持仓"
    EMPTY = "空仓"


class TradeResult(str, Enum):
    """交易结果"""
    PROFIT = "盈利"
    LOSS = "亏损"
    BREAKEVEN = "保本"
    PENDING = "未结"


class MindsetLevel(str, Enum):
    """心态评级"""
    EXCELLENT = "优秀"
    GOOD = "良好"
    NORMAL = "一般"
    POOR = "较差"
    TERRIBLE = "极差"


class MarketOutlook(str, Enum):
    """大盘预判"""
    STRONG = "强势看多"
    NEUTRAL_BULL = "震荡偏多"
    NEUTRAL = "震荡中性"
    NEUTRAL_BEAR = "震荡偏空"
    WEAK = "弱势看空"


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "低风险"
    MEDIUM = "中风险"
    HIGH = "高风险"
    EXTREME = "极高风险"


# ── 持仓记录 ─────────────────────────────────────────────

@dataclass
class PositionRecord:
    """持仓记录 — 记录当日持仓标的及交易详情"""
    ticker: str = ""                          # 股票代码
    stock_name: str = ""                      # 股票名称
    sector: str = ""                          # 所属板块/题材
    
    # 入场信息
    entry_price: float = 0.0                  # 入场点位
    entry_time: str = ""                      # 入场时间（如"09:35"）
    entry_reason: str = ""                    # 入场逻辑依据
    entry_method: str = ""                    # 入场方式（打板/低吸/半路/接力）
    
    # 出场信息
    exit_price: float = 0.0                   # 出场点位（0表示仍持仓）
    exit_time: str = ""                       # 出场时间
    exit_reason: str = ""                     # 出场原因
    
    # 盈亏信息
    position_size: float = 0.0                # 仓位比例(%)
    profit_loss_pct: float = 0.0              # 单笔盈亏幅度(%)
    profit_loss_amount: float = 0.0           # 盈亏金额
    result: TradeResult = TradeResult.PENDING  # 交易结果
    
    # 交易逻辑
    trade_logic: str = ""                     # 本次交易逻辑依据
    tactic_used: str = ""                     # 使用的战法
    
    # 失误归因
    has_error: bool = False                   # 是否有操作失误
    error_type: str = ""                      # 失误类型
    error_summary: str = ""                   # 操作失误归因总结
    
    # 备注
    notes: str = ""                           # 额外备注


# ── 交易复盘 ─────────────────────────────────────────────

@dataclass
class TradeReview:
    """当日交易复盘 — 对当日交易的完整总结"""
    date: Optional[date] = None               # 复盘日期
    
    # 持仓汇总
    positions: List[PositionRecord] = field(default_factory=list)
    total_trades: int = 0                     # 当日交易笔数
    win_count: int = 0                        # 盈利笔数
    loss_count: int = 0                       # 亏损笔数
    win_rate: float = 0.0                     # 胜率(%)
    total_pnl: float = 0.0                    # 总盈亏金额
    total_pnl_pct: float = 0.0                # 总盈亏幅度(%)
    
    # 心态复盘
    mindset_level: MindsetLevel = MindsetLevel.NORMAL  # 交易心态评级
    mindset_summary: str = ""                 # 心态总结
    rhythm_summary: str = ""                  # 交易节奏总结
    discipline_summary: str = ""              # 交易纪律总结
    
    # 问题记录
    mindset_issues: List[str] = field(default_factory=list)    # 心态问题
    rhythm_issues: List[str] = field(default_factory=list)     # 节奏问题
    discipline_issues: List[str] = field(default_factory=list) # 纪律问题
    
    # 经验总结
    lessons_learned: List[str] = field(default_factory=list)   # 经验教训
    improvements: List[str] = field(default_factory=list)      # 改进方向
    
    # 整体评价
    overall_summary: str = ""                 # 当日交易整体总结
    self_score: float = 0.0                   # 自我评分(0-100)


# ── 观察标的 ─────────────────────────────────────────────

@dataclass
class WatchStock:
    """观察标的 — 次日重点跟踪的股票"""
    ticker: str = ""                          # 股票代码
    stock_name: str = ""                      # 股票名称
    sector: str = ""                          # 所属板块
    
    # 观察原因
    watch_reason: str = ""                    # 跟踪观察原因
    expected_action: str = ""                 # 预期操作（买入/加仓/减仓/卖出）
    
    # 关键价位
    key_price: float = 0.0                    # 关键观察价位
    trigger_condition: str = ""               # 触发条件
    
    # 评分信息（可选，由评分模块提供）
    score: float = 0.0                        # 综合评分
    rating: str = ""                          # 评级
    risk_level: str = ""                      # 风险等级
    advice: str = ""                          # 操作建议
    
    # 优先级
    priority: int = 0                         # 优先级(1-5, 1最高)


# ── 次日交易计划 ─────────────────────────────────────────

@dataclass
class NextDayPlan:
    """次日交易计划 — 对次日交易的完整规划"""
    date: Optional[date] = None               # 计划日期（次日）
    created_at: Optional[datetime] = None     # 创建时间
    
    # 大盘判断
    market_outlook: MarketOutlook = MarketOutlook.NEUTRAL  # 大盘整体判断
    market_reasoning: str = ""                # 大盘判断思路
    key_levels: str = ""                      # 关键支撑/压力位
    
    # 观察标的清单
    watch_stocks: List[WatchStock] = field(default_factory=list)
    
    # 仓位管控
    total_position_limit: float = 0.0         # 整体仓位上限(%)
    single_stock_limit: float = 0.0           # 单票仓位上限(%)
    max_trades: int = 3                       # 最大交易笔数
    position_plan: str = ""                   # 仓位管控计划详情
    
    # 风控纪律
    stop_loss_rule: str = ""                  # 止损纪律
    take_profit_rule: str = ""                # 止盈纪律
    max_daily_loss: float = 0.0               # 单日最大亏损限制(%)
    risk_rules: List[str] = field(default_factory=list)  # 风控规则列表
    
    # 风险避雷
    risk_directions: List[str] = field(default_factory=list)  # 市场风险避雷方向
    avoid_sectors: List[str] = field(default_factory=list)    # 规避板块
    avoid_stocks: List[str] = field(default_factory=list)     # 规避个股
    
    # 策略方向
    preferred_sectors: List[str] = field(default_factory=list)  # 重点关注板块
    preferred_tactics: List[str] = field(default_factory=list)  # 首选战法
    
    # 备注
    notes: str = ""                           # 额外备注


# ── 完整交易笔记 ─────────────────────────────────────────

@dataclass
class TradeNote:
    """完整交易笔记 — 当日复盘 + 次日计划"""
    id: str = ""                              # 笔记ID
    date: Optional[date] = None               # 笔记日期
    
    # 当日复盘
    review: Optional[TradeReview] = None      # 交易复盘
    
    # 次日计划
    next_day_plan: Optional[NextDayPlan] = None  # 次日交易计划
    
    # 元数据
    created_at: Optional[datetime] = None     # 创建时间
    updated_at: Optional[datetime] = None     # 更新时间
    source: str = "manual"                    # 来源: manual/voice/import
    tags: List[str] = field(default_factory=list)  # 标签
    
    # 语音关联
    voice_note_id: Optional[str] = None       # 关联的语音笔记ID


# ── 语音笔记 ─────────────────────────────────────────────

@dataclass
class VoiceNote:
    """语音笔记 — 语音输入的交易记录"""
    id: str = ""                              # 语音笔记ID
    date: Optional[date] = None               # 录音日期
    created_at: Optional[datetime] = None     # 创建时间
    
    # 语音数据
    audio_data: Optional[bytes] = None        # 音频数据（二进制）
    audio_format: str = "wav"                 # 音频格式
    duration_seconds: float = 0.0             # 录音时长（秒）
    
    # 识别结果
    transcript: str = ""                      # 语音转文字结果
    parsed_type: str = ""                     # 解析类型: review/plan/mixed
    parsed_data: Optional[Dict] = None        # 解析后的结构化数据
    
    # 关联
    trade_note_id: Optional[str] = None       # 关联的交易笔记ID
    
    # 状态
    status: str = "pending"                   # 状态: pending/processing/completed/failed
    error_message: str = ""                   # 错误信息


# ── 评分请求 ─────────────────────────────────────────────

@dataclass
class ScoringRequest:
    """标的评分请求 — 用于评分决策模块"""
    ticker: str = ""                          # 股票代码
    stock_name: str = ""                      # 股票名称
    current_price: float = 0.0                # 当前价格
    
    # 上下文数据
    theme_data: Optional[Dict] = None         # 题材数据
    fund_data: Optional[Dict] = None          # 资金数据
    emotion_data: Optional[Dict] = None       # 情绪数据
    chip_data: Optional[Dict] = None          # 筹码数据
    technical_data: Optional[Dict] = None     # 技术数据
    dragon_data: Optional[Dict] = None        # 龙头数据
    news_data: Optional[Dict] = None          # 资讯数据
    
    # 用户信息
    current_position: float = 0.0             # 当前仓位(0-1)
    risk_tolerance: str = "medium"            # 风险偏好: low/medium/high


# ── 评分结果 ─────────────────────────────────────────────

@dataclass
class ScoringResult:
    """标的评分结果"""
    ticker: str = ""
    stock_name: str = ""
    current_price: float = 0.0
    
    # 评分
    total_score: float = 0.0                  # 综合评分
    rating: str = ""                          # 评级
    risk_level: str = ""                      # 风险等级
    
    # 维度评分
    dimension_scores: List[Dict] = field(default_factory=list)
    
    # 风险收益比
    risk_reward_ratio: float = 0.0
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    
    # 操作建议
    action: str = ""                          # 操作决策
    position_pct: float = 0.0                 # 建议仓位
    entry_type: str = ""                      # 入场方式
    entry_zone: str = ""                      # 入场区间
    stop_loss_strategy: str = ""              # 止损策略
    take_profit_strategy: str = ""            # 止盈策略
    
    # 风险提示
    risk_warnings: List[str] = field(default_factory=list)
    emotion_check: str = ""                   # 情绪化交易检查
    
    # 摘要
    summary: str = ""