"""统一监控引擎 — 盘中看盘核心组件

整合所有盘中监控子模块，提供一体化智能盯盘:
1. 锚定标的选择 (AnchorSelector)
2. 资金轨迹追踪 (FundTracker)
3. 预期分级评估 (ExpectationEvaluator)
4. 龙头生态监测 (EcologyMonitor)
5. 智能信号识别 (SignalDetector)
6. 出手标的锁定 (TargetLocker)
7. 操作策略生成 (StrategyGenerator)
8. 分时段提醒 (SessionAlertManager)

监控引擎工作流程:
- 盘前: 锚定标的选择 → 预期设定
- 竞价: 信号检测 → 预期评估 → 竞价提醒
- 开盘: 资金追踪 → 生态监测 → 标的锁定 → 策略生成
- 盘中: 持续监控 → 信号更新 → 策略调整
- 尾盘: 持仓决策 → 次日预判

输出: 完整的盘中监控报告，包含:
- 市场状态概览
- 锚定标的表现
- 信号汇总
- 出手标的推荐
- 操作策略
- 风险提示
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Optional, Any

from ...core.config import AppConfig
from ...core.exceptions import ModuleError
from ...core.logger import get_logger
from ...data_platform.data_models import (
    AnchorStock,
    AnchorType,
    DragonEcology,
    EmotionCycle,
    ExpectationLevel,
    FundFlowReport,
    IntradayReport,
    LimitUpStock,
    SessionAlert,
    ThemeData,
)

from .anchor_selector import AnchorSelector
from .fund_tracker import FundTracker
from .expectation_evaluator import ExpectationEvaluator
from .ecology_monitor import EcologyMonitor
from .signal_detector import SignalDetector, SignalSummary, TradingSignal
from .target_locker import TargetLocker, TargetLockReport
from .strategy_generator import StrategyGenerator, OperationPlan
from .session_alerts import SessionAlertManager, SessionType

logger = get_logger("swat.m03.watch_engine")


# ── 常量定义 ────────────────────────────────────────────

# 监控刷新间隔(秒)
MONITOR_INTERVAL_AUCTION = 60       # 竞价阶段: 1分钟
MONITOR_INTERVAL_OPEN = 30          # 开盘30分: 30秒
MONITOR_INTERVAL_MIDDAY = 120       # 盘中: 2分钟
MONITOR_INTERVAL_CLOSE = 60         # 尾盘: 1分钟

# 数据缓存时效(秒)
CACHE_TTL_ANCHORS = 3600            # 锚定标的: 1小时
CACHE_TTL_SIGNALS = 300             # 信号: 5分钟
CACHE_TTL_ECOLOGY = 600             # 生态: 10分钟


@dataclass
class MonitorContext:
    """监控上下文"""
    trade_date: Optional[date] = None
    emotion_cycle: EmotionCycle = EmotionCycle.CHAOS
    market_mood: str = "正常"
    anchors: List[AnchorStock] = field(default_factory=list)
    limit_up_stocks: List[LimitUpStock] = field(default_factory=list)
    themes: List[ThemeData] = field(default_factory=list)
    real_time_data: Dict[str, Dict] = field(default_factory=dict)
    market_snapshot: Dict = field(default_factory=dict)
    fund_report: Optional[FundFlowReport] = None
    signal_summary: Optional[SignalSummary] = None
    ecology_report: Optional[Dict] = None
    target_report: Optional[TargetLockReport] = None
    operation_plan: Optional[OperationPlan] = None
    session_alert: Optional[SessionAlert] = None
    last_update: Optional[datetime] = None


@dataclass
class WatchReport:
    """完整盘中监控报告"""
    timestamp: Optional[datetime] = None
    trade_date: Optional[date] = None
    
    # 市场概览
    market_summary: str = ""
    emotion_cycle: str = ""
    market_mood: str = ""
    ecology_health: float = 0.0
    ecology_status: str = ""
    
    # 锚定标的
    anchors: List[Dict] = field(default_factory=list)
    anchor_count: int = 0
    
    # 信号
    signal_summary_text: str = ""
    critical_signals: List[Dict] = field(default_factory=list)
    high_signals: List[Dict] = field(default_factory=list)
    opportunity_count: int = 0
    risk_count: int = 0
    
    # 出手标的
    locked_targets: List[Dict] = field(default_factory=list)
    s_grade_targets: List[Dict] = field(default_factory=list)
    a_grade_targets: List[Dict] = field(default_factory=list)
    overall_strategy: str = ""
    
    # 操作策略
    operation_plan_text: str = ""
    position_advice: str = ""
    entry_advice: List[str] = field(default_factory=list)
    risk_warnings: List[str] = field(default_factory=list)
    
    # 时段提醒
    session_alert_text: str = ""
    session_type: str = ""
    
    # 完整摘要
    full_summary: str = ""


class WatchEngine:
    """统一监控引擎
    
    整合所有盘中监控子模块，提供一体化智能盯盘。
    
    Attributes:
        config: 应用配置
        context: 监控上下文
        _sub_modules: 子模块实例
    """
    
    def __init__(self, config: Optional[AppConfig] = None):
        """初始化统一监控引擎
        
        Args:
            config: 应用配置对象
        """
        self.config = config or AppConfig()
        self.context = MonitorContext(trade_date=date.today())
        
        # 初始化子模块
        self.anchor_selector = AnchorSelector(config)
        self.fund_tracker = FundTracker(config)
        self.expectation_evaluator = ExpectationEvaluator(config)
        self.ecology_monitor = EcologyMonitor(config)
        self.signal_detector = SignalDetector(config)
        self.target_locker = TargetLocker(config)
        self.strategy_generator = StrategyGenerator(config)
        self.session_alert_manager = SessionAlertManager(config)
        
        # 缓存
        self._last_report: Optional[WatchReport] = None
        self._monitor_running = False
        
        logger.info("统一监控引擎初始化完成")
    
    # ==================== 核心公共接口 ====================
    
    async def run_monitor_cycle(
        self,
        real_time_data: Dict[str, Dict],
        limit_up_stocks: List[LimitUpStock],
        themes: List[ThemeData],
        market_snapshot: Optional[Dict] = None,
        emotion_cycle: Optional[EmotionCycle] = None,
        current_position: float = 0.0,
        daily_pnl: float = 0.0,
    ) -> WatchReport:
        """执行一次完整监控循环 — 主入口
        
        Args:
            real_time_data: 实时数据 {ticker: {...}}
            limit_up_stocks: 涨停股列表
            themes: 题材列表
            market_snapshot: 市场快照
            emotion_cycle: 情绪周期
            current_position: 当前仓位
            daily_pnl: 日内盈亏
            
        Returns:
            WatchReport: 完整监控报告
            
        Raises:
            ModuleError: 监控过程发生严重错误
        """
        logger.info("========== 开始监控循环 ==========")
        
        try:
            # 更新上下文
            self.context.real_time_data = real_time_data
            self.context.limit_up_stocks = limit_up_stocks
            self.context.themes = themes
            self.context.market_snapshot = market_snapshot or {}
            self.context.last_update = datetime.now()
            
            if emotion_cycle:
                self.context.emotion_cycle = emotion_cycle
            
            # Step 1: 锚定标的选择(如果没有或过期)
            if not self.context.anchors or self._is_cache_expired(CACHE_TTL_ANCHORS):
                logger.info("[Step 1/8] 选择锚定标的...")
                self.context.anchors = await self._select_anchors(
                    limit_up_stocks, themes
                )
            
            # Step 2: 预期分级评估
            logger.info("[Step 2/8] 评估预期...")
            await self._evaluate_expectations()
            
            # Step 3: 资金轨迹追踪
            logger.info("[Step 3/8] 追踪资金...")
            await self._track_fund_flow()
            
            # Step 4: 龙头生态监测
            logger.info("[Step 4/8] 监测生态...")
            await self._monitor_ecology()
            
            # Step 5: 智能信号识别
            logger.info("[Step 5/8] 检测信号...")
            await self._detect_signals()
            
            # Step 6: 出手标的锁定
            logger.info("[Step 6/8] 锁定标的...")
            await self._lock_targets()
            
            # Step 7: 操作策略生成
            logger.info("[Step 7/8] 生成策略...")
            await self._generate_strategy(current_position, daily_pnl)
            
            # Step 8: 分时段提醒
            logger.info("[Step 8/8] 生成时段提醒...")
            await self._generate_session_alert()
            
            # 编译报告
            report = self._compile_report()
            self._last_report = report
            
            logger.info(f"监控循环完成: 情绪{self.context.emotion_cycle.value}, "
                       f"市场{self.context.market_mood}")
            return report
            
        except Exception as e:
            logger.error(f"监控循环严重错误: {e}")
            raise ModuleError(f"监控循环失败: {e}")
    
    async def start_continuous_monitor(
        self,
        data_fetcher: callable,
        interval: Optional[int] = None,
    ):
        """启动持续监控
        
        Args:
            data_fetcher: 数据获取函数，返回(real_time_data, limit_up_stocks, themes, snapshot)
            interval: 刷新间隔(秒)，默认根据时段自动调整
        """
        self._monitor_running = True
        logger.info("持续监控已启动")
        
        while self._monitor_running:
            try:
                # 获取数据
                data = await data_fetcher()
                if data:
                    real_time_data, limit_up_stocks, themes, snapshot = data
                    
                    # 执行监控循环
                    await self.run_monitor_cycle(
                        real_time_data=real_time_data,
                        limit_up_stocks=limit_up_stocks,
                        themes=themes,
                        market_snapshot=snapshot,
                    )
                
                # 确定间隔
                actual_interval = interval or self._get_dynamic_interval()
                await asyncio.sleep(actual_interval)
                
            except asyncio.CancelledError:
                logger.info("持续监控被取消")
                break
            except Exception as e:
                logger.error(f"持续监控错误: {e}")
                await asyncio.sleep(60)  # 错误后等待1分钟
    
    def stop_monitor(self):
        """停止持续监控"""
        self._monitor_running = False
        logger.info("持续监控已停止")
    
    def get_last_report(self) -> Optional[WatchReport]:
        """获取最新报告
        
        Returns:
            Optional[WatchReport]: 最新报告
        """
        return self._last_report
    
    def get_context(self) -> MonitorContext:
        """获取监控上下文
        
        Returns:
            MonitorContext: 监控上下文
        """
        return self.context
    
    # ==================== 步骤1: 锚定标的选择 ====================
    
    async def _select_anchors(
        self,
        limit_up_stocks: List[LimitUpStock],
        themes: List[ThemeData],
    ) -> List[AnchorStock]:
        """选择锚定标的
        
        Args:
            limit_up_stocks: 涨停股
            themes: 题材
            
        Returns:
            List[AnchorStock]: 锚定标的列表
        """
        try:
            anchors = await self.anchor_selector.select_anchors(
                limit_up_stocks=limit_up_stocks,
                themes=themes,
            )
            logger.info(f"锚定标的选择完成: {len(anchors)}只")
            return anchors
        except Exception as e:
            logger.error(f"锚定标的选择失败: {e}")
            return self.context.anchors  # 返回旧的
    
    # ==================== 步骤2: 预期分级评估 ====================
    
    async def _evaluate_expectations(self):
        """执行预期分级评估"""
        try:
            results = await self.expectation_evaluator.evaluate_expectations(
                anchors=self.context.anchors,
                real_time_data=self.context.real_time_data,
                sector_data=self._build_sector_data(),
            )
            
            # 更新市场情绪
            above_count = sum(1 for r in results if r.expectation == ExpectationLevel.ABOVE)
            below_count = sum(1 for r in results if r.expectation == ExpectationLevel.BELOW)
            
            if above_count > below_count * 2:
                self.context.market_mood = "活跃"
            elif below_count > above_count * 2:
                self.context.market_mood = "低迷"
            
            logger.info(f"预期评估完成: 超预期{above_count}只, 低于预期{below_count}只")
        except Exception as e:
            logger.error(f"预期评估失败: {e}")
    
    # ==================== 步骤3: 资金轨迹追踪 ====================
    
    async def _track_fund_flow(self):
        """执行资金轨迹追踪"""
        try:
            fund_report = await self.fund_tracker.track_fund_flow(
                anchors=self.context.anchors,
                real_time_data=self.context.real_time_data,
                themes=self.context.themes,
            )
            self.context.fund_report = fund_report
            logger.info(f"资金追踪完成: 主攻{fund_report.first_direction}")
        except Exception as e:
            logger.error(f"资金追踪失败: {e}")
    
    # ==================== 步骤4: 龙头生态监测 ====================
    
    async def _monitor_ecology(self):
        """执行龙头生态监测"""
        try:
            ecology_report = await self.ecology_monitor.monitor_ecology(
                anchors=self.context.anchors,
                limit_up_stocks=self.context.limit_up_stocks,
                themes=self.context.themes,
                real_time_data=self.context.real_time_data,
            )
            
            self.context.ecology_report = {
                "health": ecology_report.overall_health,
                "status": ecology_report.overall_status,
                "gaps": [
                    {
                        "type": g.gap_type,
                        "severity": g.severity,
                        "description": g.description,
                    }
                    for g in ecology_report.gaps
                ],
                "summary": ecology_report.summary,
            }
            
            # 根据生态健康度调整市场情绪
            if ecology_report.overall_health < 30:
                self.context.market_mood = "冰点"
            elif ecology_report.overall_health >= 80:
                self.context.market_mood = "活跃"
            
            logger.info(f"生态监测完成: 健康度{ecology_report.overall_health:.1f}")
        except Exception as e:
            logger.error(f"生态监测失败: {e}")
    
    # ==================== 步骤5: 智能信号识别 ====================
    
    async def _detect_signals(self):
        """执行智能信号识别"""
        try:
            signal_summary = await self.signal_detector.detect_signals(
                anchors=self.context.anchors,
                limit_up_stocks=self.context.limit_up_stocks,
                themes=self.context.themes,
                real_time_data=self.context.real_time_data,
                market_snapshot=self.context.market_snapshot,
            )
            
            self.context.signal_summary = signal_summary
            self.context.market_mood = signal_summary.market_mood
            
            logger.info(f"信号检测完成: critical={len(signal_summary.critical_signals)}, "
                       f"high={len(signal_summary.high_signals)}")
        except Exception as e:
            logger.error(f"信号检测失败: {e}")
    
    # ==================== 步骤6: 出手标的锁定 ====================
    
    async def _lock_targets(self):
        """执行出手标的锁定"""
        try:
            # 构建信号汇总字典
            signal_dict = None
            if self.context.signal_summary:
                signal_dict = {
                    "signals": {
                        "critical": [
                            {"ticker": s.ticker, "type": s.signal_type.value}
                            for s in self.context.signal_summary.critical_signals
                        ],
                        "high": [
                            {"ticker": s.ticker, "type": s.signal_type.value}
                            for s in self.context.signal_summary.high_signals
                        ],
                    }
                }
            
            # 构建资金报告字典
            fund_dict = None
            if self.context.fund_report:
                fund_dict = {
                    "first_direction": self.context.fund_report.first_direction,
                    "second_direction": self.context.fund_report.second_direction,
                }
            
            target_report = await self.target_locker.lock_targets(
                anchors=self.context.anchors,
                limit_up_stocks=self.context.limit_up_stocks,
                themes=self.context.themes,
                real_time_data=self.context.real_time_data,
                signal_summary=signal_dict,
                fund_report=fund_dict,
                emotion_cycle=self.context.emotion_cycle,
                market_mood=self.context.market_mood,
            )
            
            self.context.target_report = target_report
            logger.info(f"标的锁定完成: S级{target_report.s_grade_count}只")
        except Exception as e:
            logger.error(f"标的锁定失败: {e}")
    
    # ==================== 步骤7: 操作策略生成 ====================
    
    async def _generate_strategy(self, current_position: float, daily_pnl: float):
        """执行操作策略生成"""
        try:
            # 构建锁定标的列表
            locked_targets = []
            if self.context.target_report:
                for target in self.context.target_report.locked_targets:
                    locked_targets.append({
                        "ticker": target.ticker,
                        "name": target.name,
                        "grade": target.grade.value,
                        "total_score": target.total_score,
                        "entry_timing": target.entry_timing.value,
                        "position_suggestion": target.position_suggestion,
                    })
            
            ecology_health = 50.0
            if self.context.ecology_report:
                ecology_health = self.context.ecology_report.get("health", 50.0)
            
            operation_plan = await self.strategy_generator.generate_strategy(
                emotion_cycle=self.context.emotion_cycle,
                market_mood=self.context.market_mood,
                anchors=self.context.anchors,
                locked_targets=locked_targets,
                ecology_health=ecology_health,
                current_position=current_position,
                daily_pnl=daily_pnl,
            )
            
            self.context.operation_plan = operation_plan
            logger.info(f"策略生成完成: {operation_plan.core_principle[:30]}...")
        except Exception as e:
            logger.error(f"策略生成失败: {e}")
    
    # ==================== 步骤8: 分时段提醒 ====================
    
    async def _generate_session_alert(self):
        """执行分时段提醒生成"""
        try:
            alert = await self.session_alert_manager.generate_session_alert(
                anchors=self.context.anchors,
                fund_report=self.context.fund_report,
                market_summary=self.context.market_snapshot,
            )
            self.context.session_alert = alert
            logger.info(f"时段提醒生成: {alert.session}")
        except Exception as e:
            logger.error(f"时段提醒生成失败: {e}")
    
    # ==================== 报告编译 ====================
    
    def _compile_report(self) -> WatchReport:
        """编译完整监控报告
        
        Returns:
            WatchReport: 完整报告
        """
        now = datetime.now()
        ctx = self.context
        
        # 市场概览
        market_summary = self._build_market_summary()
        
        # 锚定标的
        anchors_data = []
        for anchor in ctx.anchors:
            anchors_data.append({
                "ticker": anchor.ticker,
                "name": anchor.name,
                "type": anchor.anchor_type.value,
                "score": anchor.score,
                "expectation": anchor.expectation.value,
            })
        
        # 信号
        critical_signals = []
        high_signals = []
        if ctx.signal_summary:
            critical_signals = [
                {
                    "type": s.signal_type.value,
                    "ticker": s.ticker,
                    "name": s.name,
                    "description": s.description,
                    "action": s.action_suggestion,
                }
                for s in ctx.signal_summary.critical_signals
            ]
            high_signals = [
                {
                    "type": s.signal_type.value,
                    "ticker": s.ticker,
                    "name": s.name,
                    "description": s.description,
                    "action": s.action_suggestion,
                }
                for s in ctx.signal_summary.high_signals
            ]
        
        # 出手标的
        locked_targets = []
        s_grade_targets = []
        a_grade_targets = []
        if ctx.target_report:
            for target in ctx.target_report.locked_targets:
                target_dict = {
                    "ticker": target.ticker,
                    "name": target.name,
                    "grade": target.grade.value,
                    "score": target.total_score,
                    "timing": target.entry_timing.value,
                    "position": target.position_suggestion,
                    "plan": target.action_plan,
                    "risk": target.risk_warning,
                }
                locked_targets.append(target_dict)
                if target.grade.value == "S级":
                    s_grade_targets.append(target_dict)
                elif target.grade.value == "A级":
                    a_grade_targets.append(target_dict)
        
        # 操作策略
        operation_plan_text = ""
        position_advice = ""
        entry_advice = []
        risk_warnings = []
        
        if ctx.operation_plan:
            operation_plan_text = ctx.operation_plan.summary_text
            if ctx.operation_plan.position_strategy:
                position_advice = ctx.operation_plan.position_strategy.reason
            entry_advice = [
                f"{s.target_name}: {s.mode.value} — {s.reason}"
                for s in ctx.operation_plan.entry_strategies
                if s.target_name
            ]
            if ctx.operation_plan.risk_control:
                risk_warnings = ctx.operation_plan.risk_control.warnings
        
        # 时段提醒
        session_alert_text = ""
        session_type = ""
        if ctx.session_alert:
            session_alert_text = ctx.session_alert.content
            session_type = ctx.session_alert.session
        
        # 生态
        ecology_health = 0.0
        ecology_status = ""
        if ctx.ecology_report:
            ecology_health = ctx.ecology_report.get("health", 0.0)
            ecology_status = ctx.ecology_report.get("status", "")
        
        # 完整摘要
        full_summary = self._build_full_summary(
            market_summary, anchors_data, critical_signals, high_signals,
            locked_targets, operation_plan_text, session_alert_text
        )
        
        return WatchReport(
            timestamp=now,
            trade_date=ctx.trade_date,
            market_summary=market_summary,
            emotion_cycle=ctx.emotion_cycle.value,
            market_mood=ctx.market_mood,
            ecology_health=ecology_health,
            ecology_status=ecology_status,
            anchors=anchors_data,
            anchor_count=len(anchors_data),
            signal_summary_text=ctx.signal_summary.summary_text if ctx.signal_summary else "",
            critical_signals=critical_signals,
            high_signals=high_signals,
            opportunity_count=len(ctx.signal_summary.key_opportunities) if ctx.signal_summary else 0,
            risk_count=len(ctx.signal_summary.key_risks) if ctx.signal_summary else 0,
            locked_targets=locked_targets,
            s_grade_targets=s_grade_targets,
            a_grade_targets=a_grade_targets,
            overall_strategy=ctx.target_report.overall_strategy if ctx.target_report else "",
            operation_plan_text=operation_plan_text,
            position_advice=position_advice,
            entry_advice=entry_advice,
            risk_warnings=risk_warnings,
            session_alert_text=session_alert_text,
            session_type=session_type,
            full_summary=full_summary,
        )
    
    def _build_market_summary(self) -> str:
        """构建市场概览
        
        Returns:
            str: 市场概览
        """
        ctx = self.context
        parts: List[str] = []
        
        parts.append(f"情绪周期: {ctx.emotion_cycle.value}")
        parts.append(f"市场情绪: {ctx.market_mood}")
        
        snapshot = ctx.market_snapshot
        if snapshot:
            limit_up = snapshot.get("limit_up_count", 0)
            limit_down = snapshot.get("limit_down_count", 0)
            parts.append(f"涨停{limit_up}只/跌停{limit_down}只")
            
            volume_status = snapshot.get("volume_status", "")
            if volume_status:
                parts.append(f"量能: {volume_status}")
        
        return " | ".join(parts)
    
    def _build_full_summary(
        self,
        market_summary: str,
        anchors: List[Dict],
        critical_signals: List[Dict],
        high_signals: List[Dict],
        locked_targets: List[Dict],
        operation_plan: str,
        session_alert: str,
    ) -> str:
        """构建完整摘要
        
        Returns:
            str: 完整摘要
        """
        now = datetime.now()
        parts: List[str] = []
        
        parts.append(f"╔══════════════════════════════════════╗")
        parts.append(f"║   盘中智能监控报告 [{now.strftime('%H:%M:%S')}]              ║")
        parts.append(f"╚══════════════════════════════════════╝")
        parts.append("")
        
        # 市场概览
        parts.append(f"📊 市场概览")
        parts.append(f"   {market_summary}")
        parts.append("")
        
        # 紧急信号
        if critical_signals:
            parts.append(f"⚠️ 紧急信号 ({len(critical_signals)}条)")
            for sig in critical_signals[:3]:
                parts.append(f"   • {sig['description']}")
                parts.append(f"     → {sig['action']}")
            parts.append("")
        
        # 重点信号
        if high_signals:
            parts.append(f"🔥 重点信号 ({len(high_signals)}条)")
            for sig in high_signals[:5]:
                parts.append(f"   • {sig['description']}")
            parts.append("")
        
        # S级标的
        s_targets = [t for t in locked_targets if t.get("grade") == "S级"]
        if s_targets:
            parts.append(f"💎 S级出手标的")
            for t in s_targets[:3]:
                parts.append(f"   • {t['name']}({t['ticker']}) — {t['timing']}")
                parts.append(f"     仓位: {t['position']} | {t['plan']}")
            parts.append("")
        
        # A级标的
        a_targets = [t for t in locked_targets if t.get("grade") == "A级"]
        if a_targets:
            parts.append(f"⭐ A级出手标的")
            for t in a_targets[:3]:
                parts.append(f"   • {t['name']}({t['ticker']}) — {t['timing']}")
            parts.append("")
        
        # 操作策略
        if operation_plan:
            parts.append(f"📋 操作策略")
            for line in operation_plan.split("\n")[:8]:
                parts.append(f"   {line}")
            parts.append("")
        
        # 时段提醒
        if session_alert:
            parts.append(f"🔔 时段提醒")
            for line in session_alert.split("\n")[:5]:
                parts.append(f"   {line}")
        
        return "\n".join(parts)
    
    # ==================== 辅助方法 ====================
    
    def _build_sector_data(self) -> Dict[str, Dict]:
        """构建板块数据
        
        Returns:
            Dict[str, Dict]: 板块数据
        """
        sector_data: Dict[str, Dict] = {}
        
        for theme in self.context.themes:
            sector_data[theme.theme_name] = {
                "avg_change": theme.avg_change_pct,
                "limit_up_count": theme.limit_up_count,
            }
        
        return sector_data
    
    def _is_cache_expired(self, ttl: int) -> bool:
        """检查缓存是否过期
        
        Args:
            ttl: 缓存时效(秒)
            
        Returns:
            bool: 是否过期
        """
        if not self.context.last_update:
            return True
        elapsed = (datetime.now() - self.context.last_update).total_seconds()
        return elapsed > ttl
    
    def _get_dynamic_interval(self) -> int:
        """获取动态刷新间隔
        
        Returns:
            int: 间隔(秒)
        """
        session = self.session_alert_manager.get_current_session()
        
        if session == SessionType.AUCTION:
            return MONITOR_INTERVAL_AUCTION
        elif session == SessionType.OPEN_30MIN:
            return MONITOR_INTERVAL_OPEN
        elif session == SessionType.CLOSE:
            return MONITOR_INTERVAL_CLOSE
        else:
            return MONITOR_INTERVAL_MIDDAY
    
    def reset(self):
        """重置监控引擎"""
        self.context = MonitorContext(trade_date=date.today())
        self._last_report = None
        self.anchor_selector.clear_cache()
        self.fund_tracker.clear_cache()
        self.expectation_evaluator.clear_evaluations()
        self.ecology_monitor.clear_cache()
        self.signal_detector.clear_history()
        self.session_alert_manager.clear_history()
        logger.info("监控引擎已重置")