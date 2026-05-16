"""资讯采集模块数据模型 — 定义NewsItem、ScoredNews、RiskWarningList、PreMarketSummary等核心数据结构"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional


# ==================== 枚举定义 ====================

class NewsCategory(str, Enum):
    """资讯分类"""
    POLICY = "政策"          # 政策/监管/宏观
    GLOBAL = "外围"          # 外围市场/外围
    FUND = "资金"            # 资金动向/流向
    THEME = "题材"           # 题材催化/行业
    STOCK = "个股"           # 个股公告/业绩
    SENTIMENT = "舆情"       # 市场情绪/舆情


class NewsGrade(str, Enum):
    """资讯价值等级"""
    S = "S"  # 高价值 (score >= 75%)
    A = "A"  # 较高价值 (50% <= score < 75%)
    B = "B"  # 一般价值 (25% <= score < 50%)
    C = "C"  # 低价值 (score < 25%)


class RiskLevel(str, Enum):
    """风险预警等级"""
    FORBIDDEN = "绝对禁入"    # 严禁买入
    HIGH = "高度谨慎"         # 高度谨慎对待
    LOW = "轻度警示"          # 轻度警示关注


# ==================== 核心数据模型 ====================

@dataclass
class NewsSource:
    """资讯来源信息"""
    name: str = ""           # 来源名称，如 "财联社"
    url: str = ""            # 来源链接
    source_type: str = ""    # 官方/媒体/社区/公告
    credibility: float = 0.0 # 可信度评分 0-100


@dataclass
class NewsItem:
    """单条原始资讯条目
    
    Attributes:
        id: 唯一标识
        title: 资讯标题
        content: 资讯正文摘要
        category: 资讯分类（政策/外围/资金/题材/个股/舆情）
        source: 资讯来源信息
        publish_time: 发布时间
        trade_date: 关联交易日
        related_tickers: 关联个股代码列表
        related_themes: 关联题材列表
        keywords: 关键词标签
        raw_metadata: 原始元数据（扩展用）
    """
    id: str = ""
    title: str = ""
    content: str = ""
    category: NewsCategory = NewsCategory.POLICY
    source: NewsSource = field(default_factory=NewsSource)
    publish_time: Optional[datetime] = None
    trade_date: Optional[date] = None
    related_tickers: List[str] = field(default_factory=list)
    related_themes: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    raw_metadata: Dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """后初始化校验"""
        if not self.id:
            self.id = f"news_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(self.title) & 0xFFFF:04X}"


@dataclass
class ScoredNews:
    """被打分的资讯条目
    
    Attributes:
        news: 原始资讯
        score: 回测驱动综合得分 0-100
        grade: 等级 S/A/B/C
        score_details: 分项得分详情
        backtest_evidence: 回测证据支撑
        recommendation: 操作建议摘要
    """
    news: NewsItem = field(default_factory=NewsItem)
    score: float = 0.0
    grade: NewsGrade = NewsGrade.C
    score_details: Dict = field(default_factory=dict)
    backtest_evidence: List[str] = field(default_factory=list)
    recommendation: str = ""

    def __post_init__(self) -> None:
        """根据得分自动确定等级"""
        if self.score >= 75:
            self.grade = NewsGrade.S
        elif self.score >= 50:
            self.grade = NewsGrade.A
        elif self.score >= 25:
            self.grade = NewsGrade.B
        else:
            self.grade = NewsGrade.C


@dataclass
class RiskWarning:
    """单条风险预警"""
    level: RiskLevel = RiskLevel.LOW
    ticker: str = ""         # 涉及个股代码（如为空则是系统性风险）
    stock_name: str = ""     # 股票名称
    reason: str = ""         # 风险原因描述
    trigger_source: str = "" # 触发来源（资讯ID/公告类型等）
    advice: str = ""         # 应对建议


@dataclass
class RiskWarningList:
    """当日完整避雷清单"""
    trade_date: Optional[date] = None
    forbidden: List[RiskWarning] = field(default_factory=list)   # 绝对禁入
    high_risk: List[RiskWarning] = field(default_factory=list)   # 高度谨慎
    low_risk: List[RiskWarning] = field(default_factory=list)    # 轻度警示
    system_risk_summary: str = ""  # 系统性风险总结

    @property
    def total_count(self) -> int:
        """预警总数"""
        return len(self.forbidden) + len(self.high_risk) + len(self.low_risk)

    @property
    def forbidden_tickers(self) -> List[str]:
        """获取绝对禁入的股票代码列表"""
        return [r.ticker for r in self.forbidden if r.ticker]

    @property
    def all_tickers(self) -> List[str]:
        """获取所有涉及的股票代码（去重）"""
        tickers: List[str] = []
        for risk in self.forbidden + self.high_risk + self.low_risk:
            if risk.ticker and risk.ticker not in tickers:
                tickers.append(risk.ticker)
        return tickers


@dataclass
class PreMarketSummary:
    """盘前资讯汇总输出
    
    Attributes:
        trade_date: 交易日
        overall_summary: 整体盘前综述
        policy_digest: 政策监管摘要
        global_digest: 外围市场摘要
        fund_digest: 资金动向摘要
        theme_digest: 题材催化摘要
        stock_announcements: 重要个股公告摘要
        sentiment_digest: 市场情绪摘要
        risk_warnings: 风险预警摘要
        scored_highlights: 高价值资讯列表（S级+A级）
        key_themes: 今日重点关注题材
        market_sentiment: 市场整体情绪判断
    """
    trade_date: Optional[date] = None
    overall_summary: str = ""
    policy_digest: str = ""
    global_digest: str = ""
    fund_digest: str = ""
    theme_digest: str = ""
    stock_announcements: List[Dict] = field(default_factory=list)
    sentiment_digest: str = ""
    risk_warnings: List[str] = field(default_factory=list)
    scored_highlights: List[ScoredNews] = field(default_factory=list)
    key_themes: List[str] = field(default_factory=list)
    market_sentiment: str = ""
