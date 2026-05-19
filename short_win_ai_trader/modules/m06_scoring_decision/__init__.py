"""评分决策模块 (m06_scoring_decision)

为超短选手提供多维度标的评分和操作建议:
- 7大维度综合评分: 题材强度/资金匹配/情绪周期/筹码结构/技术形态/龙头地位/资讯催化
- 风险收益比评估: 三重止损体系 + 动态止盈
- 操作建议生成: 仓位/入场/止损止盈/持有卖出条件
- 情绪化交易防范: FOMO/报复性交易/恐慌性卖出检测

核心组件:
- ScoringEngine: 统一评分引擎，整合所有维度评分
- DimensionScorers: 各维度独立评分器
- RiskRewardCalculator: 风险收益比计算器
- TradePlanner: 交易计划生成器

使用方式:
    from short_win_ai_trader.modules.m06_scoring_decision import ScoringEngine
    
    engine = ScoringEngine()
    report = await engine.evaluate_stock(
        ticker="000001.SZ",
        stock_name="平安银行",
        current_price=12.50,
        theme_data={"theme_level": "部委级", "sustainability": "发酵中", ...},
        fund_data={"main_net_inflow": 3000, "volume_ratio": 2.5, ...},
        emotion_data={"current_cycle": "发酵", "profit_effect": "好", ...},
        chip_data={"chip_concentration": 60, "trapped_ratio": 20, ...},
        technical_data={"ma_arrangement": "多头排列", "breakout_type": "平台突破", ...},
        dragon_data={"dragon_type": "分支龙头", "board_count": 3, ...},
        news_data={"catalyst_level": "重要", "timeliness": "当日", ...},
    )
    print(report.summary_text)
"""

from .dimension_scorers import (
    DIMENSION_WEIGHTS,
    ChipStructureScorer,
    DimensionScore,
    DragonStatusScorer,
    EmotionCycleScorer,
    FundMatchScorer,
    NewsCatalystScorer,
    TechnicalScorer,
    ThemeStrengthScorer,
)
from .scoring_engine import (
    ActionDecision,
    OperationAdvice,
    RatingLevel,
    RiskLevel,
    RiskRewardResult,
    ScoringEngine,
    ScoringReport,
)

# 兼容旧接口
from .scorer import ComprehensiveScorer
from .risk_reward import RiskRewardCalculator
from .position_manager import PositionManager
from .trade_planner import TradePlanner

__all__ = [
    # 新接口
    "ScoringEngine",
    "ScoringReport",
    "RatingLevel",
    "ActionDecision",
    "RiskLevel",
    "RiskRewardResult",
    "OperationAdvice",
    "DimensionScore",
    "DIMENSION_WEIGHTS",
    # 维度评分器
    "ThemeStrengthScorer",
    "FundMatchScorer",
    "EmotionCycleScorer",
    "ChipStructureScorer",
    "TechnicalScorer",
    "DragonStatusScorer",
    "NewsCatalystScorer",
    # 旧接口(兼容)
    "ComprehensiveScorer",
    "RiskRewardCalculator",
    "PositionManager",
    "TradePlanner",
]