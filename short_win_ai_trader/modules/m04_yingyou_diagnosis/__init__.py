"""模块四: 游资模式诊断系统 (M04)

功能:
    - 8大顶级游资完整数字指纹
    - 游资视角盘面诊断(情绪x资金x模式)
    - 标的游资匹配度评分
    - 游资共识分析
    - 分级组合策略(新手/进阶/高手)

导出:
    - FingerprintRegistry: 游资指纹注册中心
    - YingYouDiagnosisEngine: 诊断引擎
    - YingYouRecommender: 推荐引擎
    - ConsensusAnalyzer: 共识分析器
    - PortfolioStrategyEngine: 组合策略引擎
"""

from .consensus import (
    ConsensusAnalyzer,
    ConsensusPool,
    ConsensusReport,
    ConsensusSignal,
    DivergenceAlert,
    consensus_analyzer,
    consensus_pool,
)
from .diagnosis import (
    DiagnosisReport,
    EmotionPhase,
    EmotionPhaseDetector,
    FundDirection,
    FundDirectionAnalyzer,
    ModeFitCalculator,
    ModeFitScore,
    YingYouDiagnosisEngine,
    diagnosis_engine,
)
from .fingerprints import (
    FingerprintRegistry,
    YingYouFingerprint,
    registry,
)
from .portfolio import (
    PortfolioConfig,
    PortfolioConfigFactory,
    PortfolioExecution,
    PortfolioStrategy,
    PortfolioStrategyEngine,
    portfolio_engine,
)
from .recommender import (
    DimensionScorer,
    StockYingYouMatch,
    YingYouRecommender,
    recommender,
)

__all__ = [
    # fingerprints
    "FingerprintRegistry",
    "YingYouFingerprint",
    "registry",
    # diagnosis
    "YingYouDiagnosisEngine",
    "EmotionPhase",
    "EmotionPhaseDetector",
    "FundDirection",
    "FundDirectionAnalyzer",
    "ModeFitScore",
    "ModeFitCalculator",
    "DiagnosisReport",
    "diagnosis_engine",
    # recommender
    "YingYouRecommender",
    "StockYingYouMatch",
    "DimensionScorer",
    "recommender",
    # consensus
    "ConsensusAnalyzer",
    "ConsensusPool",
    "ConsensusReport",
    "ConsensusSignal",
    "DivergenceAlert",
    "consensus_analyzer",
    "consensus_pool",
    # portfolio
    "PortfolioStrategyEngine",
    "PortfolioConfig",
    "PortfolioConfigFactory",
    "PortfolioStrategy",
    "PortfolioExecution",
    "portfolio_engine",
]
