"""模块一：全域资讯智能采集

提供全维度资讯采集、评分、风险检测和盘前汇总功能。
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

__all__ = [
    "NewsCollector",
    "NewsItem",
    "NewsSource",
    "NewsCategory",
    "NewsGrade",
    "ScoredNews",
    "RiskWarning",
    "RiskWarningList",
    "RiskLevel",
    "RiskDetector",
    "RiskRule",
    "NewsScorer",
    "ScoreDimension",
    "ScoreResult",
    "PreMarketSummary",
]
