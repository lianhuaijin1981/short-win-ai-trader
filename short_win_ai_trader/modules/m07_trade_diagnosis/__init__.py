"""交割单诊断模块 (m07_trade_diagnosis)

为超短选手提供交易诊断和能力提升方案:
- 交割单导入: 支持CSV/Excel/手动录入多种格式
- 交易画像: 客观评价交易风格、胜率、盈亏比
- 高频错误归因: 识别交易中的高频错误类型
- 错误交易诊断: 结合评分决策模块逐笔分析
- K线/分时图标注: 可视化指出交易错误
- 改进建议: 针对性改进意见
- 模拟训练计划: 个性化训练方案

核心组件:
- TradeImporter: 交割单数据导入器
- TradeProfiler: 交易画像分析器
- ErrorAttribution: 高频错误类型归因
- TradeDiagnoser: 错误交易诊断器
- ChartAnnotator: K线/分时图错误标注
- ImprovementAdvisor: 改进建议生成器
- TrainingPlanner: 模拟训练计划生成器
- DiagnosisEngine: 统一诊断引擎

使用方式:
    from short_win_ai_trader.modules.m07_trade_diagnosis import DiagnosisEngine
    
    engine = DiagnosisEngine()
    # 导入交割单
    trades = await engine.import_trades("trades.csv")
    # 生成诊断报告
    report = await engine.diagnose(trades)
    print(report.summary)
"""

from .importer import TradeImporter, TradeRecord
from .profiler import TradeProfiler, TradeProfile
from .error_attribution import ErrorAttribution, ErrorType, ErrorPattern, AttributionResult
from .trade_diagnoser import TradeDiagnoser, TradeDiagnosis
from .chart_annotator import ChartAnnotator, ChartAnnotation, ChartPoint
from .improvement_advisor import ImprovementAdvisor, ImprovementPlan, ImprovementAction
from .training_planner import TrainingPlanner, TrainingPlan, TrainingTask, TrainingWeek
from .diagnosis_engine import DiagnosisEngine, DiagnosisReport

__all__ = [
    # 核心引擎
    "DiagnosisEngine",
    "DiagnosisReport",
    # 数据导入
    "TradeImporter",
    "TradeRecord",
    # 交易画像
    "TradeProfiler",
    "TradeProfile",
    # 错误归因
    "ErrorAttribution",
    "ErrorType",
    "ErrorPattern",
    "AttributionResult",
    # 交易诊断
    "TradeDiagnoser",
    "TradeDiagnosis",
    # 图表标注
    "ChartAnnotator",
    "ChartAnnotation",
    "ChartPoint",
    # 改进建议
    "ImprovementAdvisor",
    "ImprovementPlan",
    "ImprovementAction",
    # 训练计划
    "TrainingPlanner",
    "TrainingPlan",
    "TrainingTask",
    "TrainingWeek",
]