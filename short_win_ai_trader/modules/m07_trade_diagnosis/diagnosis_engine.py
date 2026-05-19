"""统一诊断引擎

整合所有诊断组件，提供一站式交易诊断服务:
1. 导入交割单数据
2. 生成交易画像
3. 高频错误归因
4. 逐笔交易诊断
5. K线/分时图标注
6. 生成改进建议
7. 生成训练计划

使用方式:
    from short_win_ai_trader.modules.m07_trade_diagnosis import DiagnosisEngine
    
    engine = DiagnosisEngine()
    
    # 导入交割单
    trades = await engine.import_trades("trades.csv")
    
    # 生成完整诊断报告
    report = await engine.diagnose(trades)
    print(report.summary)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from ...core.logger import get_logger
from .chart_annotator import ChartAnnotator, ChartAnnotation
from .error_attribution import ErrorAttribution, AttributionResult
from .improvement_advisor import ImprovementAdvisor, ImprovementPlan
from .importer import TradeImporter, TradeRecord
from .profiler import TradeProfiler, TradeProfile
from .trade_diagnoser import TradeDiagnoser, TradeDiagnosis
from .training_planner import TrainingPlanner, TrainingPlan

logger = get_logger("swat.m07.diagnosis_engine")


# ── 数据模型 ─────────────────────────────────────────────

@dataclass
class DiagnosisReport:
    """完整诊断报告"""
    # 基本信息
    report_id: str = ""                   # 报告ID
    generated_at: Optional[datetime] = None  # 生成时间
    total_trades: int = 0                 # 总交易数
    
    # 交易画像
    profile: Optional[TradeProfile] = None
    
    # 错误归因
    attribution: Optional[AttributionResult] = None
    
    # 交易诊断
    diagnoses: List[TradeDiagnosis] = field(default_factory=list)
    
    # 图表标注
    annotations: List[ChartAnnotation] = field(default_factory=list)
    
    # 改进建议
    improvement: Optional[ImprovementPlan] = None
    
    # 训练计划
    training: Optional[TrainingPlan] = None
    
    # 统计摘要
    error_trades: int = 0                 # 错误交易数
    correct_trades: int = 0               # 正确交易数
    total_loss_from_errors: float = 0.0   # 错误导致总亏损
    
    # 报告摘要
    summary: str = ""


# ── 统一诊断引擎 ─────────────────────────────────────────

class DiagnosisEngine:
    """统一诊断引擎
    
    整合所有诊断组件，提供一站式服务。
    """
    
    def __init__(self):
        """初始化诊断引擎"""
        self.importer = TradeImporter()
        self.profiler = TradeProfiler()
        self.attribution = ErrorAttribution()
        self.diagnoser = TradeDiagnoser()
        self.annotator = ChartAnnotator()
        self.advisor = ImprovementAdvisor()
        self.trainer = TrainingPlanner()
        
        self._report_counter = 0
        logger.info("统一诊断引擎初始化完成")
    
    # ==================== 数据导入 ====================
    
    async def import_trades(self, file_path: str) -> List[TradeRecord]:
        """导入交割单
        
        Args:
            file_path: 文件路径(CSV/JSON)
            
        Returns:
            List[TradeRecord]: 交易记录列表
        """
        if file_path.endswith('.csv'):
            return await self.importer.import_from_csv(file_path)
        elif file_path.endswith('.json'):
            return await self.importer.import_from_json(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {file_path}")
    
    def manual_entry(self, **kwargs) -> TradeRecord:
        """手动录入交易
        
        Args:
            **kwargs: 交易参数
            
        Returns:
            TradeRecord: 交易记录
        """
        return self.importer.manual_entry(**kwargs)
    
    def batch_entry(self, entries: List[Dict]) -> List[TradeRecord]:
        """批量录入交易
        
        Args:
            entries: 交易参数列表
            
        Returns:
            List[TradeRecord]: 交易记录列表
        """
        return self.importer.batch_manual_entry(entries)
    
    # ==================== 完整诊断 ====================
    
    async def diagnose(
        self,
        trades: List[TradeRecord],
        market_contexts: Optional[Dict[str, Dict]] = None,
        kline_data: Optional[Dict[str, List[Dict]]] = None,
        intraday_data: Optional[Dict[str, List[Dict]]] = None,
    ) -> DiagnosisReport:
        """生成完整诊断报告
        
        Args:
            trades: 交易记录列表
            market_contexts: 各交易的市场环境 {trade_id: context}
            kline_data: K线数据 {ticker: kline_list}
            intraday_data: 分时数据 {ticker: intraday_list}
            
        Returns:
            DiagnosisReport: 完整诊断报告
        """
        if not trades:
            raise ValueError("无交易记录")
        
        self._report_counter += 1
        logger.info(f"========== 开始诊断报告 R{self._report_counter:04d}: {len(trades)}笔交易 ==========")
        
        report = DiagnosisReport(
            report_id=f"R{self._report_counter:04d}",
            generated_at=datetime.now(),
            total_trades=len(trades),
        )
        
        # Step 1: 生成交易画像
        logger.info("[Step 1/7] 生成交易画像...")
        report.profile = self.profiler.generate_profile(trades)
        
        # Step 2: 高频错误归因
        logger.info("[Step 2/7] 高频错误归因...")
        report.attribution = self.attribution.analyze(trades)
        
        # Step 3: 逐笔交易诊断
        logger.info("[Step 3/7] 逐笔交易诊断...")
        report.diagnoses = await self.diagnoser.diagnose_all_trades(trades, market_contexts)
        
        # Step 4: 图表标注
        logger.info("[Step 4/7] 图表标注...")
        for trade, diagnosis in zip(trades, report.diagnoses):
            ticker = trade.ticker
            kline = kline_data.get(ticker) if kline_data else None
            intraday = intraday_data.get(ticker) if intraday_data else None
            
            annotation = self.annotator.annotate(trade, diagnosis, kline, intraday)
            report.annotations.append(annotation)
        
        # Step 5: 统计
        logger.info("[Step 5/7] 统计汇总...")
        report.error_trades = sum(1 for d in report.diagnoses if d.is_error_trade)
        report.correct_trades = len(report.diagnoses) - report.error_trades
        report.total_loss_from_errors = sum(
            d.profit_loss for d in report.diagnoses if d.is_error_trade
        )
        
        # Step 6: 改进建议
        logger.info("[Step 6/7] 生成改进建议...")
        report.improvement = self.advisor.generate_plan(
            report.profile, report.attribution, report.diagnoses
        )
        
        # Step 7: 训练计划
        logger.info("[Step 7/7] 生成训练计划...")
        report.training = self.trainer.generate_plan(
            report.profile, report.attribution, report.improvement
        )
        
        # 生成摘要
        report.summary = self._build_summary(report)
        
        logger.info(f"诊断报告 R{self._report_counter:04d} 生成完成")
        return report
    
    # ==================== 单独诊断 ====================
    
    async def diagnose_single(
        self,
        trade: TradeRecord,
        market_context: Optional[Dict] = None,
        kline_data: Optional[List[Dict]] = None,
        intraday_data: Optional[List[Dict]] = None,
    ) -> TradeDiagnosis:
        """诊断单笔交易
        
        Args:
            trade: 交易记录
            market_context: 市场环境
            kline_data: K线数据
            intraday_data: 分时数据
            
        Returns:
            TradeDiagnosis: 交易诊断
        """
        diagnosis = await self.diagnoser.diagnose_trade(trade, market_context)
        return diagnosis
    
    def get_profile(self, trades: List[TradeRecord]) -> TradeProfile:
        """获取交易画像
        
        Args:
            trades: 交易记录列表
            
        Returns:
            TradeProfile: 交易画像
        """
        return self.profiler.generate_profile(trades)
    
    def get_attribution(self, trades: List[TradeRecord]) -> AttributionResult:
        """获取错误归因
        
        Args:
            trades: 交易记录列表
            
        Returns:
            AttributionResult: 归因结果
        """
        return self.attribution.analyze(trades)
    
    # ==================== 摘要生成 ====================
    
    def _build_summary(self, report: DiagnosisReport) -> str:
        """构建报告摘要"""
        parts: List[str] = []
        
        parts.append(f"╔══════════════════════════════════════════════╗")
        parts.append(f"║        交易诊断报告 [{report.report_id}]              ║")
        parts.append(f"║        生成时间: {report.generated_at.strftime('%Y-%m-%d %H:%M') if report.generated_at else ''}              ║")
        parts.append(f"╚══════════════════════════════════════════════╝")
        parts.append("")
        
        # 交易统计
        parts.append(f"📊 交易统计:")
        parts.append(f"   总交易: {report.total_trades}笔")
        parts.append(f"   错误交易: {report.error_trades}笔 ({report.error_trades/report.total_trades*100:.0f}%)")
        parts.append(f"   正确交易: {report.correct_trades}笔 ({report.correct_trades/report.total_trades*100:.0f}%)")
        parts.append(f"   错误导致亏损: {abs(report.total_loss_from_errors):.0f}元")
        parts.append("")
        
        # 画像摘要
        if report.profile:
            parts.append(f"🎯 交易画像:")
            parts.append(f"   风格: {report.profile.style}")
            parts.append(f"   胜率: {report.profile.win_rate}%")
            parts.append(f"   盈亏比: {report.profile.profit_loss_ratio}")
            parts.append(f"   综合评分: {report.profile.overall_score}分")
            parts.append("")
        
        # 错误归因摘要
        if report.attribution and report.attribution.top_errors:
            parts.append(f"🔴 Top错误:")
            for i, pattern in enumerate(report.attribution.top_errors[:3], 1):
                parts.append(f"   {i}. {pattern.error_type.value}: {abs(pattern.total_loss):.0f}元 ({pattern.frequency}次)")
            parts.append("")
        
        # 改进建议摘要
        if report.improvement:
            parts.append(f"💡 改进建议:")
            parts.append(f"   当前水平: {report.improvement.current_level}")
            parts.append(f"   目标水平: {report.improvement.current_level}")
            if report.improvement.top_priorities:
                parts.append(f"   优先改进: {report.improvement.top_priorities[0]}")
            parts.append("")
        
        # 训练计划摘要
        if report.training:
            parts.append(f"📅 训练计划:")
            parts.append(f"   训练周期: {report.training.total_weeks}周")
            parts.append(f"   训练重点: {', '.join(report.training.focus_areas)}")
            parts.append("")
        
        # 分隔线
        parts.append(f"{'='*50}")
        parts.append(f"详细报告请查看各模块输出")
        
        return "\n".join(parts)