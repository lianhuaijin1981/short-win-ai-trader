"""模块二：全维度智能复盘 + 市场情绪 & 题材周期研判

提供全自动复盘、情绪周期研判、题材周期分析和大盘趋势推演功能。

核心功能:
- 情绪周期研判: 六段周期识别、情绪趋势分析、极端值预警
- 题材周期分析: 题材生命周期、关联度分析、轮动速度分析
- 大盘趋势推演: 多因子预判、量价背离检测、技术指标分析
- 智能复盘: 历史对比、复盘质量评分、统计信息
"""

from .emotion_engine import EmotionEngine, CYCLE_CONFIG
from .market_predictor import MarketPredictor, TechnicalContext
from .replay import BoardLadder, MarketReplay, MarketReplayReport
from .theme_analyzer import ThemeAnalyzer

__all__ = [
    "MarketReplay",
    "MarketReplayReport",
    "BoardLadder",
    "EmotionEngine",
    "CYCLE_CONFIG",
    "ThemeAnalyzer",
    "MarketPredictor",
    "TechnicalContext",
]
