"""操作策略生成器 — 盘中看盘核心组件

根据情绪周期、生态状态、信号汇总和出手标的，
为超短选手生成针对性的操作策略:
- 仓位管理策略（总仓位、单票仓位）
- 出手策略（打板/低吸/半路/接力）
- 持仓策略（锁仓/加仓/减仓/清仓）
- 风控策略（止损/止盈/应急）

策略核心原则:
- 情绪启动期: 积极试错，打板为主
- 情绪发酵期: 加仓龙头，持股待涨
- 情绪高潮期: 逐步止盈，不追高
- 情绪分歧期: 去弱留强，低吸核心
- 情绪退潮期: 管住手，空仓或极轻仓
- 情绪混沌期: 观察为主，等待方向
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from ...core.config import AppConfig
from ...core.exceptions import ModuleError
from ...core.logger import get_logger
from ...data_platform.data_models import (
    AnchorStock,
    AnchorType,
    EmotionCycle,
    ExpectationLevel,
)

logger = get_logger("swat.m03.strategy_generator")


# ── 常量定义 ────────────────────────────────────────────

# 仓位上限配置(按情绪周期)
POSITION_LIMIT = {
    EmotionCycle.CHAOS: 0.2,      # 混沌期: 20%
    EmotionCycle.START: 0.5,      # 启动期: 50%
    EmotionCycle.FERMENT: 0.7,    # 发酵期: 70%
    EmotionCycle.PEAK: 0.5,       # 高潮期: 50%(逐步减仓)
    EmotionCycle.DIVERGE: 0.4,    # 分歧期: 40%
    EmotionCycle.RETREAT: 0.1,    # 退潮期: 10%
}

# 单票仓位上限
SINGLE_POSITION_LIMIT = {
    EmotionCycle.CHAOS: 0.1,
    EmotionCycle.START: 0.2,
    EmotionCycle.FERMENT: 0.3,
    EmotionCycle.PEAK: 0.2,
    EmotionCycle.DIVERGE: 0.15,
    EmotionCycle.RETREAT: 0.05,
}

# 止损止盈配置
STOP_LOSS_PCT = -5.0              # 通用止损
TAKE_PROFIT_PCT = 15.0            # 通用止盈
DRAGON_STOP_LOSS = -8.0           # 龙头止损(更宽)
DRAGON_TAKE_PROFIT = 25.0         # 龙头止盈(更高)


class OperationMode(str, Enum):
    """操作模式"""
    BOARD_HIT = "打板"
    LOW_ABSORB = "低吸"
    HALF_WAY = "半路"
    RELAY = "接力"
    HOLD = "锁仓"
    ADD_POSITION = "加仓"
    REDUCE_POSITION = "减仓"
    CLEAR_POSITION = "清仓"
    WAIT = "观望"


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "低风险"
    MEDIUM = "中风险"
    HIGH = "高风险"
    EXTREME = "极高风险"


@dataclass
class PositionStrategy:
    """仓位管理策略"""
    total_position_limit: float = 0.0       # 总仓位上限(0-1)
    single_position_limit: float = 0.0      # 单票仓位上限
    current_position: float = 0.0           # 当前仓位
    action: str = ""                        # 仓位操作: 加仓/减仓/维持
    reason: str = ""


@dataclass
class EntryStrategy:
    """出手策略"""
    mode: OperationMode = OperationMode.WAIT
    target_ticker: str = ""
    target_name: str = ""
    entry_price_zone: str = ""              # 入场价格区间
    position_pct: float = 0.0               # 建议仓位比例
    stop_loss: float = 0.0                  # 止损价
    take_profit: float = 0.0                # 止盈价
    confidence: float = 0.0                 # 置信度
    reason: str = ""


@dataclass
class HoldStrategy:
    """持仓策略"""
    ticker: str = ""
    name: str = ""
    action: OperationMode = OperationMode.HOLD
    current_profit: float = 0.0             # 当前盈亏
    action_reason: str = ""
    hold_conditions: List[str] = field(default_factory=list)    # 继续持有条件
    sell_conditions: List[str] = field(default_factory=list)    # 卖出条件


@dataclass
class RiskControlStrategy:
    """风控策略"""
    risk_level: RiskLevel = RiskLevel.MEDIUM
    max_drawdown_limit: float = 0.0         # 最大回撤限制
    daily_loss_limit: float = 0.0           # 日内亏损限制
    emergency_plan: str = ""                # 应急预案
    warnings: List[str] = field(default_factory=list)


@dataclass
class OperationPlan:
    """完整操作策略"""
    timestamp: Optional[datetime] = None
    emotion_cycle: str = ""
    market_mood: str = ""
    position_strategy: Optional[PositionStrategy] = None
    entry_strategies: List[EntryStrategy] = field(default_factory=list)
    hold_strategies: List[HoldStrategy] = field(default_factory=list)
    risk_control: Optional[RiskControlStrategy] = None
    core_principle: str = ""                # 核心原则
    summary_text: str = ""


class StrategyGenerator:
    """操作策略生成器
    
    根据市场状态生成完整的操作策略。
    
    Attributes:
        config: 应用配置
        _current_position: 当前仓位
    """
    
    def __init__(self, config: Optional[AppConfig] = None):
        """初始化操作策略生成器
        
        Args:
            config: 应用配置对象
        """
        self.config = config or AppConfig()
        self._current_position = 0.0
        self._daily_pnl = 0.0
        logger.info("操作策略生成器初始化完成")
    
    # ==================== 核心公共接口 ====================
    
    async def generate_strategy(
        self,
        emotion_cycle: EmotionCycle,
        market_mood: str,
        anchors: List[AnchorStock],
        locked_targets: List[Dict],
        signal_summary: Optional[Dict] = None,
        ecology_health: float = 50.0,
        current_position: float = 0.0,
        daily_pnl: float = 0.0,
    ) -> OperationPlan:
        """生成操作策略主入口
        
        Args:
            emotion_cycle: 情绪周期
            market_mood: 市场情绪
            anchors: 锚定标的
            locked_targets: 锁定标的列表
            signal_summary: 信号汇总
            ecology_health: 生态健康度
            current_position: 当前仓位(0-1)
            daily_pnl: 日内盈亏
            
        Returns:
            OperationPlan: 操作策略
            
        Raises:
            ModuleError: 生成过程发生严重错误
        """
        logger.info("========== 开始生成操作策略 ==========")
        
        try:
            self._current_position = current_position
            self._daily_pnl = daily_pnl
            
            # Step 1: 仓位管理策略
            logger.info("[Step 1/4] 生成仓位管理策略...")
            position_strategy = self._generate_position_strategy(
                emotion_cycle, market_mood, ecology_health
            )
            
            # Step 2: 出手策略
            logger.info("[Step 2/4] 生成出手策略...")
            entry_strategies = self._generate_entry_strategies(
                emotion_cycle, locked_targets, anchors, signal_summary
            )
            
            # Step 3: 持仓策略
            logger.info("[Step 3/4] 生成持仓策略...")
            hold_strategies = self._generate_hold_strategies(
                emotion_cycle, anchors, signal_summary
            )
            
            # Step 4: 风控策略
            logger.info("[Step 4/4] 生成风控策略...")
            risk_control = self._generate_risk_control(
                emotion_cycle, market_mood, ecology_health, daily_pnl
            )
            
            # 核心原则
            core_principle = self._get_core_principle(emotion_cycle)
            
            # 生成摘要
            summary = self._compile_summary(
                emotion_cycle, market_mood, position_strategy,
                entry_strategies, hold_strategies, risk_control, core_principle
            )
            
            plan = OperationPlan(
                timestamp=datetime.now(),
                emotion_cycle=emotion_cycle.value,
                market_mood=market_mood,
                position_strategy=position_strategy,
                entry_strategies=entry_strategies,
                hold_strategies=hold_strategies,
                risk_control=risk_control,
                core_principle=core_principle,
                summary_text=summary,
            )
            
            logger.info(f"操作策略生成完成: {core_principle}")
            return plan
            
        except Exception as e:
            logger.error(f"操作策略生成严重错误: {e}")
            raise ModuleError(f"操作策略生成失败: {e}")
    
    # ==================== 步骤1: 仓位管理 ====================
    
    def _generate_position_strategy(
        self,
        emotion_cycle: EmotionCycle,
        market_mood: str,
        ecology_health: float,
    ) -> PositionStrategy:
        """生成仓位管理策略
        
        Args:
            emotion_cycle: 情绪周期
            market_mood: 市场情绪
            ecology_health: 生态健康度
            
        Returns:
            PositionStrategy: 仓位策略
        """
        # 基础仓位上限
        position_limit = POSITION_LIMIT.get(emotion_cycle, 0.3)
        single_limit = SINGLE_POSITION_LIMIT.get(emotion_cycle, 0.15)
        
        # 根据生态健康度调整
        if ecology_health >= 80:
            position_limit = min(1.0, position_limit * 1.2)
        elif ecology_health < 40:
            position_limit = max(0.05, position_limit * 0.5)
        
        # 根据市场情绪调整
        if market_mood == "冰点":
            position_limit = min(position_limit, 0.2)
        elif market_mood == "高潮":
            position_limit = min(position_limit, 0.5)
        
        # 仓位操作建议
        current = self._current_position
        if current < position_limit * 0.5:
            action = "加仓"
            reason = f"当前仓位{current:.0%}，低于建议上限{position_limit:.0%}，可加仓"
        elif current > position_limit:
            action = "减仓"
            reason = f"当前仓位{current:.0%}，超过建议上限{position_limit:.0%}，需减仓"
        else:
            action = "维持"
            reason = f"当前仓位{current:.0%}，在建议范围内"
        
        return PositionStrategy(
            total_position_limit=position_limit,
            single_position_limit=single_limit,
            current_position=current,
            action=action,
            reason=reason,
        )
    
    # ==================== 步骤2: 出手策略 ====================
    
    def _generate_entry_strategies(
        self,
        emotion_cycle: EmotionCycle,
        locked_targets: List[Dict],
        anchors: List[AnchorStock],
        signal_summary: Optional[Dict] = None,
    ) -> List[EntryStrategy]:
        """生成出手策略
        
        Args:
            emotion_cycle: 情绪周期
            locked_targets: 锁定标的
            anchors: 锚定标的
            signal_summary: 信号汇总
            
        Returns:
            List[EntryStrategy]: 出手策略列表
        """
        strategies: List[EntryStrategy] = []
        
        # 退潮期不出手
        if emotion_cycle == EmotionCycle.RETREAT:
            strategies.append(EntryStrategy(
                mode=OperationMode.WAIT,
                reason="退潮期，管住手，不出手",
                confidence=1.0,
            ))
            return strategies
        
        # 根据锁定标的生成出手策略
        anchor_map = {a.ticker: a for a in anchors}
        
        for target in locked_targets[:3]:  # 只取前3个
            ticker = target.get("ticker", "")
            name = target.get("name", "")
            grade = target.get("grade", "C级")
            score = target.get("total_score", 0)
            entry_timing = target.get("entry_timing", "")
            position_suggestion = target.get("position_suggestion", "")
            
            anchor = anchor_map.get(ticker)
            
            # 确定操作模式
            mode = self._determine_entry_mode(
                emotion_cycle, entry_timing, anchor
            )
            
            # 仓位比例
            position_pct = self._parse_position(position_suggestion)
            
            # 止损止盈
            if anchor and anchor.anchor_type == AnchorType.TOTAL_DRAGON:
                stop_loss = DRAGON_STOP_LOSS
                take_profit = DRAGON_TAKE_PROFIT
            else:
                stop_loss = STOP_LOSS_PCT
                take_profit = TAKE_PROFIT_PCT
            
            # 置信度
            confidence = min(1.0, score / 100)
            
            # 入场价格区间
            entry_zone = self._determine_entry_zone(mode, entry_timing)
            
            # 理由
            reason = self._generate_entry_reason(
                grade, mode, emotion_cycle, entry_timing
            )
            
            strategies.append(EntryStrategy(
                mode=mode,
                target_ticker=ticker,
                target_name=name,
                entry_price_zone=entry_zone,
                position_pct=position_pct,
                stop_loss=stop_loss,
                take_profit=take_profit,
                confidence=confidence,
                reason=reason,
            ))
        
        # 如果没有锁定标的
        if not strategies:
            strategies.append(EntryStrategy(
                mode=OperationMode.WAIT,
                reason="无合适出手标的，观望等待",
                confidence=0.5,
            ))
        
        return strategies
    
    def _determine_entry_mode(
        self,
        emotion_cycle: EmotionCycle,
        entry_timing: str,
        anchor: Optional[AnchorStock],
    ) -> OperationMode:
        """确定操作模式
        
        Args:
            emotion_cycle: 情绪周期
            entry_timing: 出手时机
            anchor: 锚定标的
            
        Returns:
            OperationMode: 操作模式
        """
        # 根据时机
        if "竞价" in entry_timing or "开盘" in entry_timing:
            if emotion_cycle in (EmotionCycle.START, EmotionCycle.FERMENT):
                return OperationMode.BOARD_HIT  # 启动/发酵期打板
            else:
                return OperationMode.HALF_WAY   # 其他期半路
        
        if "回封" in entry_timing:
            return OperationMode.RELAY  # 回封接力
        
        if "分歧" in entry_timing or "低吸" in entry_timing:
            return OperationMode.LOW_ABSORB  # 分歧低吸
        
        if "突破" in entry_timing:
            return OperationMode.HALF_WAY  # 突破半路
        
        if "冰点" in entry_timing:
            return OperationMode.BOARD_HIT  # 冰点试错打板
        
        # 根据情绪周期默认
        if emotion_cycle == EmotionCycle.START:
            return OperationMode.BOARD_HIT
        elif emotion_cycle == EmotionCycle.FERMENT:
            return OperationMode.RELAY
        elif emotion_cycle == EmotionCycle.DIVERGE:
            return OperationMode.LOW_ABSORB
        else:
            return OperationMode.WAIT
    
    def _parse_position(self, position_suggestion: str) -> float:
        """解析仓位建议
        
        Args:
            position_suggestion: 仓位建议字符串
            
        Returns:
            float: 仓位比例
        """
        if "50-70" in position_suggestion:
            return 0.6
        elif "30-50" in position_suggestion:
            return 0.4
        elif "10-30" in position_suggestion:
            return 0.2
        elif "观察" in position_suggestion:
            return 0.0
        return 0.3
    
    def _determine_entry_zone(self, mode: OperationMode, timing: str) -> str:
        """确定入场价格区间
        
        Args:
            mode: 操作模式
            timing: 出手时机
            
        Returns:
            str: 价格区间描述
        """
        if mode == OperationMode.BOARD_HIT:
            return "涨停价排队或打板确认"
        elif mode == OperationMode.LOW_ABSORB:
            return "分时均线下方-3%至-5%区间"
        elif mode == OperationMode.HALF_WAY:
            return "分时突破前高或涨幅3-5%区间"
        elif mode == OperationMode.RELAY:
            return "回封确认时或炸板后回封瞬间"
        return "等待明确信号"
    
    def _generate_entry_reason(
        self,
        grade: str,
        mode: OperationMode,
        emotion_cycle: EmotionCycle,
        timing: str,
    ) -> str:
        """生成出手理由
        
        Args:
            grade: 标的分级
            mode: 操作模式
            emotion_cycle: 情绪周期
            timing: 出手时机
            
        Returns:
            str: 出手理由
        """
        parts: List[str] = []
        parts.append(f"{grade}标的")
        parts.append(f"{mode.value}模式")
        parts.append(f"情绪{emotion_cycle.value}")
        parts.append(f"时机: {timing}")
        return " | ".join(parts)
    
    # ==================== 步骤3: 持仓策略 ====================
    
    def _generate_hold_strategies(
        self,
        emotion_cycle: EmotionCycle,
        anchors: List[AnchorStock],
        signal_summary: Optional[Dict] = None,
    ) -> List[HoldStrategy]:
        """生成持仓策略
        
        Args:
            emotion_cycle: 情绪周期
            anchors: 锚定标的
            signal_summary: 信号汇总
            
        Returns:
            List[HoldStrategy]: 持仓策略列表
        """
        strategies: List[HoldStrategy] = []
        
        for anchor in anchors:
            expectation = anchor.expectation
            
            # 根据预期和情绪周期决定操作
            if expectation == ExpectationLevel.BELOW:
                if emotion_cycle in (EmotionCycle.RETREAT, EmotionCycle.DIVERGE):
                    action = OperationMode.CLEAR_POSITION
                    reason = "低于预期+退潮/分歧期，清仓"
                else:
                    action = OperationMode.REDUCE_POSITION
                    reason = "低于预期，减仓观察"
                
                hold_conditions = []
                sell_conditions = [
                    "反抽至成本价附近减仓",
                    "跌破止损位立即清仓",
                    "板块整体走弱清仓",
                ]
            
            elif expectation == ExpectationLevel.ABOVE:
                if emotion_cycle in (EmotionCycle.FERMENT, EmotionCycle.START):
                    action = OperationMode.ADD_POSITION
                    reason = "超预期+发酵/启动期，可加仓"
                else:
                    action = OperationMode.HOLD
                    reason = "超预期，锁仓持有"
                
                hold_conditions = [
                    "涨停继续持有",
                    "板块效应维持持有",
                    "量价健康持有",
                ]
                sell_conditions = [
                    "断板减仓",
                    "板块效应消失清仓",
                    "达到止盈位分批止盈",
                ]
            
            else:  # 符合预期
                action = OperationMode.HOLD
                reason = "符合预期，按计划持有"
                
                hold_conditions = [
                    "走势正常继续持有",
                    "板块配合持有",
                ]
                sell_conditions = [
                    "走弱减仓",
                    "达到止盈位止盈",
                    "跌破止损位止损",
                ]
            
            strategies.append(HoldStrategy(
                ticker=anchor.ticker,
                name=anchor.name,
                action=action,
                action_reason=reason,
                hold_conditions=hold_conditions,
                sell_conditions=sell_conditions,
            ))
        
        return strategies
    
    # ==================== 步骤4: 风控策略 ====================
    
    def _generate_risk_control(
        self,
        emotion_cycle: EmotionCycle,
        market_mood: str,
        ecology_health: float,
        daily_pnl: float,
    ) -> RiskControlStrategy:
        """生成风控策略
        
        Args:
            emotion_cycle: 情绪周期
            market_mood: 市场情绪
            ecology_health: 生态健康度
            daily_pnl: 日内盈亏
            
        Returns:
            RiskControlStrategy: 风控策略
        """
        # 风险等级
        if emotion_cycle == EmotionCycle.RETREAT:
            risk_level = RiskLevel.EXTREME
        elif ecology_health < 30:
            risk_level = RiskLevel.HIGH
        elif market_mood == "冰点":
            risk_level = RiskLevel.HIGH
        elif emotion_cycle in (EmotionCycle.START, EmotionCycle.FERMENT):
            risk_level = RiskLevel.LOW
        else:
            risk_level = RiskLevel.MEDIUM
        
        # 最大回撤限制
        max_drawdown = {
            RiskLevel.LOW: 0.10,
            RiskLevel.MEDIUM: 0.08,
            RiskLevel.HIGH: 0.05,
            RiskLevel.EXTREME: 0.03,
        }.get(risk_level, 0.08)
        
        # 日内亏损限制
        daily_loss_limit = {
            RiskLevel.LOW: 0.05,
            RiskLevel.MEDIUM: 0.03,
            RiskLevel.HIGH: 0.02,
            RiskLevel.EXTREME: 0.01,
        }.get(risk_level, 0.03)
        
        # 应急预案
        warnings: List[str] = []
        emergency_parts: List[str] = []
        
        if daily_pnl < -daily_loss_limit:
            warnings.append(f"日内亏损已达{abs(daily_pnl):.1%}，接近限制")
            emergency_parts.append("立即停止开新仓")
        
        if ecology_health < 30:
            warnings.append("生态健康度低，梯队可能崩塌")
            emergency_parts.append("减仓至安全仓位")
        
        if market_mood == "冰点":
            warnings.append("情绪冰点，注意控制风险")
            emergency_parts.append("只保留最强标的")
        
        if not emergency_parts:
            emergency_parts.append("按止损止盈纪律执行")
        
        return RiskControlStrategy(
            risk_level=risk_level,
            max_drawdown_limit=max_drawdown,
            daily_loss_limit=daily_loss_limit,
            emergency_plan="; ".join(emergency_parts),
            warnings=warnings,
        )
    
    # ==================== 辅助方法 ====================
    
    def _get_core_principle(self, emotion_cycle: EmotionCycle) -> str:
        """获取核心操作原则
        
        Args:
            emotion_cycle: 情绪周期
            
        Returns:
            str: 核心原则
        """
        principles = {
            EmotionCycle.CHAOS: "混沌期——观察为主，等待方向明确，不轻易出手",
            EmotionCycle.START: "启动期——积极试错，打板先锋龙，小仓位快进快出",
            EmotionCycle.FERMENT: "发酵期——加仓龙头，持股待涨，享受主升浪",
            EmotionCycle.PEAK: "高潮期——逐步止盈，不追高，去弱留强",
            EmotionCycle.DIVERGE: "分歧期——低吸核心，去弱留强，等待分歧转一致",
            EmotionCycle.RETREAT: "退潮期——管住手，空仓或极轻仓，等待冰点",
        }
        return principles.get(emotion_cycle, "观察为主")
    
    def _compile_summary(
        self,
        emotion_cycle: EmotionCycle,
        market_mood: str,
        position_strategy: PositionStrategy,
        entry_strategies: List[EntryStrategy],
        hold_strategies: List[HoldStrategy],
        risk_control: RiskControlStrategy,
        core_principle: str,
    ) -> str:
        """编译策略摘要
        
        Args:
            emotion_cycle: 情绪周期
            market_mood: 市场情绪
            position_strategy: 仓位策略
            entry_strategies: 出手策略
            hold_strategies: 持仓策略
            risk_control: 风控策略
            core_principle: 核心原则
            
        Returns:
            str: 策略摘要
        """
        now = datetime.now()
        parts: List[str] = []
        
        parts.append(f"=== 操作策略 [{now.strftime('%H:%M')}] ===")
        parts.append(f"情绪周期: {emotion_cycle.value}")
        parts.append(f"市场情绪: {market_mood}")
        parts.append(f"核心原则: {core_principle}")
        parts.append("")
        
        # 仓位
        parts.append(f"仓位: 上限{position_strategy.total_position_limit:.0%}, "
                     f"当前{position_strategy.current_position:.0%}, "
                     f"建议{position_strategy.action}")
        
        # 出手
        entry_modes = [s.mode.value for s in entry_strategies if s.mode != OperationMode.WAIT]
        if entry_modes:
            parts.append(f"出手: {', '.join(entry_modes)}")
        else:
            parts.append("出手: 观望")
        
        # 持仓
        for hs in hold_strategies[:3]:
            parts.append(f"  {hs.name}: {hs.action.value} — {hs.action_reason}")
        
        # 风控
        parts.append(f"风控: {risk_control.risk_level.value}, "
                     f"日内亏损限制{risk_control.daily_loss_limit:.0%}")
        
        if risk_control.warnings:
            parts.append(f"⚠️ 预警: {'; '.join(risk_control.warnings)}")
        
        return "\n".join(parts)
    
    def set_current_position(self, position: float):
        """设置当前仓位
        
        Args:
            position: 仓位比例(0-1)
        """
        self._current_position = max(0, min(1, position))
    
    def set_daily_pnl(self, pnl: float):
        """设置日内盈亏
        
        Args:
            pnl: 盈亏比例
        """
        self._daily_pnl = pnl