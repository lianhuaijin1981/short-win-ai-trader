"""模块一：全域资讯智能采集

提供全维度资讯采集、评分、风险检测和盘前汇总功能。

新增功能 (v2.0):
- 多源资讯采集器: 支持10+重要资讯来源并行采集
- 历史回测引擎: 基于历史数据评估消息类型对股价的影响
- 利好介入建议: 对重要利好资讯提供具体操作建议
- 利空风险预警: 对重大利空资讯提供风险预警
"""

from .collector import NewsCollector
from .models import (
    NewsCategory,
    NewsGrade,
    NewsItem,
    NewsSource,
    PreMarketSummary,
    RiskLevel,
    RiskWarning,
    RiskWarningList,
    ScoredNews,
)
from .risk_detector import RiskDetector, RiskRule
from .scorer import NewsScorer, ScoreDimension, ScoreResult

# v2.0 新增组件
from .backtest_engine import (
    BacktestEngine,
    BacktestResult,
    MessageImpactProfile,
    MESSAGE_TYPE_PROFILES,
)
from .multi_source_fetcher import (
    MultiSourceFetcher,
    BaseSourceFetcher,
    CninfoFetcher,
    CLSFetcher,
    EastmoneyFetcher,
    XueqiuFetcher,
    TaogubaFetcher,
    KaiPanLaFetcher,
    NEWS_SOURCES_CONFIG,
)
from .recommendation_engine import (
    RecommendationEngine,
    EntryRecommendationGenerator,
    RiskAlertGenerator,
    EntryRecommendation,
    RiskAlert,
)

__all__ = [
    # 核心组件
    "NewsCollector",
    "NewsItem",
    "NewsSource",
    "NewsCategory",
    "NewsGrade",
    "ScoredNews",
    # 风险检测
    "RiskWarning",
    "RiskWarningList",
    "RiskLevel",
    "RiskDetector",
    "RiskRule",
    # 评分
    "NewsScorer",
    "ScoreDimension",
    "ScoreResult",
    "PreMarketSummary",
    # v2.0: 历史回测引擎
    "BacktestEngine",
    "BacktestResult",
    "MessageImpactProfile",
    "MESSAGE_TYPE_PROFILES",
    # v2.0: 多源采集器
    "MultiSourceFetcher",
    "BaseSourceFetcher",
    "CninfoFetcher",
    "CLSFetcher",
    "EastmoneyFetcher",
    "XueqiuFetcher",
    "TaogubaFetcher",
    "KaiPanLaFetcher",
    "NEWS_SOURCES_CONFIG",
    # v2.0: 建议引擎
    "RecommendationEngine",
    "EntryRecommendationGenerator",
    "RiskAlertGenerator",
    "EntryRecommendation",
    "RiskAlert",
]
