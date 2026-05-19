"""模块三: 盘中看盘 — 实时监控与决策支持

核心功能:
- 锚定标的智能锁定 (anchor_selector)
- 资金轨迹追踪 (fund_tracker)
- 预期分级评估 (expectation_evaluator)
- 龙头生态梯队监测 (ecology_monitor)
- 智能信号识别 (signal_detector) — 新增
- 出手标的锁定 (target_locker) — 新增
- 操作策略生成 (strategy_generator) — 新增
- 分时段提醒 (session_alerts)
- 统一监控引擎 (watch_engine) — 新增

使用流程:
1. 盘前/开盘后调用 anchor_selector 生成锚定标的池
2. 盘中定时调用 fund_tracker 追踪资金流向
3. 实时监控 ecology_monitor 评估梯队健康度
4. signal_detector 实时检测盘口信号
5. target_locker 锁定最佳出手标的
6. strategy_generator 生成操作策略
7. 使用 watch_engine 统一调度所有模块
"""

from .anchor_selector import (
    AnchorCandidate,
    AnchorPool,
    AnchorSelector,
)
from .ecology_monitor import (
    EcologyMonitor,
    EcologyReport,
    TierGap,
    TierHealth,
)
from .expectation_evaluator import (
    ExpectationCriteria,
    ExpectationEvaluator,
    ExpectationResult,
)
from .fund_tracker import (
    FundFlowReport,
    FundFlowSnapshot,
    FundFlowSummary,
    FundTrack,
    FundTracker,
    SectorAlert,
)
from .session_alerts import (
    AuctionAnalysis,
    CloseAnalysis,
    MiddayAnalysis,
    Open30MinAnalysis,
    SessionAlertManager,
    SessionType,
)
from .signal_detector import (
    SignalDetector,
    SignalPriority,
    SignalSummary,
    SignalType,
    TradingSignal,
)
from .target_locker import (
    EntryTiming,
    LockedTarget,
    TargetGrade,
    TargetLocker,
    TargetLockReport,
    TargetScore,
)
from .strategy_generator import (
    EntryStrategy,
    HoldStrategy,
    OperationMode,
    OperationPlan,
    PositionStrategy,
    RiskControlStrategy,
    RiskLevel,
    StrategyGenerator,
)
from .watch_engine import (
    MonitorContext,
    WatchEngine,
    WatchReport,
)

__all__ = [
    # 锚定标的选择器
    "AnchorSelector",
    "AnchorPool",
    "AnchorCandidate",
    # 资金追踪
    "FundTracker",
    "FundFlowReport",
    "FundFlowSummary",
    "FundFlowSnapshot",
    "FundTrack",
    "SectorAlert",
    # 预期评估
    "ExpectationEvaluator",
    "ExpectationResult",
    "ExpectationCriteria",
    # 生态监测
    "EcologyMonitor",
    "EcologyReport",
    "TierHealth",
    "TierGap",
    # 信号识别 — 新增
    "SignalDetector",
    "SignalType",
    "SignalPriority",
    "TradingSignal",
    "SignalSummary",
    # 出手标的锁定 — 新增
    "TargetLocker",
    "TargetGrade",
    "EntryTiming",
    "TargetScore",
    "LockedTarget",
    "TargetLockReport",
    # 操作策略 — 新增
    "StrategyGenerator",
    "OperationMode",
    "RiskLevel",
    "PositionStrategy",
    "EntryStrategy",
    "HoldStrategy",
    "RiskControlStrategy",
    "OperationPlan",
    # 时段提醒
    "SessionAlertManager",
    "SessionType",
    "AuctionAnalysis",
    "Open30MinAnalysis",
    "MiddayAnalysis",
    "CloseAnalysis",
    # 统一监控引擎 — 新增
    "WatchEngine",
    "MonitorContext",
    "WatchReport",
]