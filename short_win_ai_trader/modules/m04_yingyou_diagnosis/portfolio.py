"""游资组合策略 — 不同水平的交易者适配不同游资组合

组合策略分为三个等级:
    1. 新手组合(退学炒股 + 92科比): 
       - 核心思路: 严控风险，提高胜率
       - 仓位上限: 50%
       - 单笔上限: 5%
       - 止损严格: -5%铁律
    
    2. 进阶组合(炒股养家 + 小鳄鱼):
       - 核心思路: 情绪周期+打板结合，稳定盈利
       - 仓位上限: 70%
       - 单笔上限: 30%
       - 止损规则: -3%或破支撑
    
    3. 高手组合(Asking + 职业炒手):
       - 核心思路: 只做最强，追求暴利
       - 仓位上限: 90%
       - 单笔上限: 50%
       - 止损规则: 断板即走

每种组合包含:
    - 游资配置比例
    - 选股策略
    - 仓位管理
    - 风险控制
    - 预期收益
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from api.core.logger import get_logger

from .consensus import ConsensusAnalyzer, ConsensusPool
from .diagnosis import YingYouDiagnosisEngine, diagnosis_engine
from .fingerprints import YingYouFingerprint, registry
from .recommender import YingYouRecommender, recommender

logger = get_logger("swat.m04.portfolio")


# ═══════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════

@dataclass
class PortfolioConfig:
    """组合配置"""
    level: str                          # 等级: 新手/进阶/高手
    yingyou_allocation: Dict[str, float]  # 游资配置比例
    max_position: int                   # 最大仓位(%)
    single_position_limit: int          # 单笔仓位上限(%)
    stop_loss_rule: str                 # 止损规则
    take_profit_rule: str               # 止盈规则
    daily_trade_limit: int              # 每日最大交易次数
    empty_condition: str                # 空仓条件
    core_philosophy: str                # 核心思路
    expected_return_monthly: str        # 预期月收益
    max_drawdown_limit: int             # 最大回撤限制(%)


@dataclass
class PortfolioStrategy:
    """组合策略详情"""
    level: str
    config: PortfolioConfig
    primary_yingyou: List[Dict]       # 主要游资详情
    current_diagnosis: Dict           # 当前盘面诊断
    today_plan: List[Dict]            # 今日计划
    risk_reminder: List[str]          # 风险提醒


@dataclass
class PortfolioExecution:
    """组合执行方案"""
    level: str
    total_position: int               # 总仓位建议
    positions: List[Dict]             # 具体仓位分配
    entry_plan: List[Dict]            # 入场计划
    exit_plan: List[Dict]             # 出场计划
    emergency_plan: str               # 应急方案
    review_criteria: List[str]        # 复盘标准


# ═══════════════════════════════════════════════════════════
# 组合配置工厂
# ═══════════════════════════════════════════════════════════

class PortfolioConfigFactory:
    """组合配置工厂 — 生成不同等级的组合配置"""

    @classmethod
    def create_beginner(cls) -> PortfolioConfig:
        """新手组合: 退学炒股 + 92科比"""
        return PortfolioConfig(
            level="新手",
            yingyou_allocation={
                "退学炒股": 0.60,    # 超跌+空仓策略为主
                "92科比": 0.40,      # 计划交易回调低吸
            },
            max_position=50,
            single_position_limit=5,
            stop_loss_rule="-5%严格止损，不犹豫",
            take_profit_rule="反弹10-15%分批止盈",
            daily_trade_limit=2,
            empty_condition="连续3天亏损或情绪退潮期",
            core_philosophy=(
                "新手以求存为先，通过退学炒股的空仓纪律控制回撤，"
                "通过92科比的计划交易提高胜率。"
                "核心目标: 不亏钱，小赚就是胜利"
            ),
            expected_return_monthly="3-8%",
            max_drawdown_limit=5,
        )

    @classmethod
    def create_intermediate(cls) -> PortfolioConfig:
        """进阶组合: 炒股养家 + 小鳄鱼"""
        return PortfolioConfig(
            level="进阶",
            yingyou_allocation={
                "炒股养家": 0.55,    # 情绪周期定仓位
                "小鳄鱼": 0.45,      # 打板做龙头
            },
            max_position=70,
            single_position_limit=30,
            stop_loss_rule="-3%或破支撑位止损",
            take_profit_rule="断板即走，高潮日减仓",
            daily_trade_limit=3,
            empty_condition="情绪退潮或炸板率>60%",
            core_philosophy=(
                "进阶以稳定盈利为目标，通过炒股养家的情绪周期理论"
                "把握市场节奏，通过小鳄鱼的打板模式抓取确定性机会。"
                "核心目标: 稳定月盈利5-15%"
            ),
            expected_return_monthly="8-15%",
            max_drawdown_limit=8,
        )

    @classmethod
    def create_advanced(cls) -> PortfolioConfig:
        """高手组合: Asking + 职业炒手"""
        return PortfolioConfig(
            level="高手",
            yingyou_allocation={
                "Asking": 0.50,      # 只做龙头追涨
                "职业炒手": 0.50,    # 只做最强连板
            },
            max_position=90,
            single_position_limit=50,
            stop_loss_rule="断板即走，低开-5%止损",
            take_profit_rule="连板持有，不连板不恋战",
            daily_trade_limit=3,
            empty_condition="弱市(涨停<30家)空仓",
            core_philosophy=(
                "高手追求暴利，只做市场最强标的。"
                "Asking的龙头信仰+职业炒手的连板信仰，"
                "在市场好的时候重仓出击，市场差时空仓休息。"
                "核心目标: 抓住龙头主升浪，单月20%+"
            ),
            expected_return_monthly="15-30%",
            max_drawdown_limit=12,
        )

    @classmethod
    def get_config(cls, level: str) -> Optional[PortfolioConfig]:
        """根据等级获取配置"""
        factories = {
            "新手": cls.create_beginner,
            "进阶": cls.create_intermediate,
            "高手": cls.create_advanced,
            "beginner": cls.create_beginner,
            "intermediate": cls.create_intermediate,
            "advanced": cls.create_advanced,
        }
        factory = factories.get(level)
        return factory() if factory else None


# ═══════════════════════════════════════════════════════════
# 组合策略引擎
# ═══════════════════════════════════════════════════════════

class PortfolioStrategyEngine:
    """组合策略引擎 — 生成完整的组合策略方案"""

    def __init__(self):
        self.factory = PortfolioConfigFactory()
        self.diagnosis = diagnosis_engine
        self.recommender = recommender

    async def generate_strategy(self, level: str) -> PortfolioStrategy:
        """生成指定等级的组合策略"""
        logger.info(f"Generating portfolio strategy for level={level}")

        config = self.factory.get_config(level)
        if not config:
            raise ValueError(f"Unknown level: {level}")

        # 获取盘面诊断
        diag_report = await self.diagnosis.diagnose()

        # 获取主要游资详情
        primary = []
        for yingyou_name, ratio in config.yingyou_allocation.items():
            fp = registry.get(yingyou_name)
            if fp:
                primary.append({
                    "name": yingyou_name,
                    "ratio": f"{ratio*100:.0f}%",
                    "philosophy": fp.philosophy,
                    "position_limit": f"{fp.position_limit}%",
                    "key_tactic": fp.classic_tactics[0]["name"] if fp.classic_tactics else "",
                    "radar": fp.radar_scores,
                })

        # 今日计划
        today_plan = self._gen_today_plan(config, diag_report)

        # 风险提醒
        risk_reminder = self._gen_risk_reminder(config, diag_report)

        return PortfolioStrategy(
            level=level,
            config=config,
            primary_yingyou=primary,
            current_diagnosis={
                "emotion_phase": diag_report.emotion_phase.phase,
                "confidence": diag_report.emotion_phase.confidence,
                "primary_direction": diag_report.fund_direction.primary_direction,
                "position_suggestion": diag_report.emotion_phase.position_suggestion,
            },
            today_plan=today_plan,
            risk_reminder=risk_reminder,
        )

    async def generate_execution(
        self,
        level: str,
        tickers: Optional[List[Dict[str, str]]] = None,
    ) -> PortfolioExecution:
        """生成可执行方案"""
        config = self.factory.get_config(level)
        if not config:
            raise ValueError(f"Unknown level: {level}")

        # 盘面诊断
        diag = await self.diagnosis.diagnose()

        # 根据情绪阶段确定仓位
        emotion_position = self._emotion_to_position(
            diag.emotion_phase.phase, config.max_position
        )

        # 仓位分配
        positions = self._allocate_positions(config, emotion_position)

        # 入场计划
        entry_plan = await self._gen_entry_plan(config, diag, tickers)

        # 出场计划
        exit_plan = self._gen_exit_plan(config, diag)

        # 应急方案
        emergency = self._gen_emergency_plan(config, diag)

        # 复盘标准
        review = self._gen_review_criteria(config)

        return PortfolioExecution(
            level=level,
            total_position=emotion_position,
            positions=positions,
            entry_plan=entry_plan,
            exit_plan=exit_plan,
            emergency_plan=emergency,
            review_criteria=review,
        )

    def _gen_today_plan(
        self,
        config: PortfolioConfig,
        diag,
    ) -> List[Dict]:
        """生成今日计划"""
        plans = []
        phase = diag.emotion_phase.phase

        # 早盘计划
        plans.append({
            "time": "09:25",
            "action": "竞价观察",
            "content": f"观察竞价强度，确认{phase}期判断",
            "key_points": ["涨停委买额", "竞价涨跌比", "题材竞价强度"],
        })

        # 根据阶段调整
        if phase in ["修复", "高潮"]:
            plans.append({
                "time": "09:30-10:30",
                "action": "开仓/加仓",
                "content": f"按计划介入，总仓位不超过{config.max_position}%",
                "key_points": ["打板标的", "低吸标的", "仓位控制"],
            })
        elif phase == "冰点":
            plans.append({
                "time": "09:30-10:30",
                "action": "试探性建仓",
                "content": "小仓位试探，等待情绪企稳",
                "key_points": ["超跌标的", "题材共振", "轻仓试探"],
            })
        else:  # 退潮
            plans.append({
                "time": "09:30-10:30",
                "action": "减仓/空仓",
                "content": "退潮期不新开仓，持仓减仓",
                "key_points": ["持仓处理", "不追热点", "等待冰点"],
            })

        # 午盘计划
        plans.append({
            "time": "13:00-14:30",
            "action": "持仓管理",
            "content": "处理持仓，不新增",
            "key_points": ["止盈止损", "持仓去弱留强"],
        })

        # 尾盘计划
        plans.append({
            "time": "14:30-15:00",
            "action": "尾盘确认",
            "content": "确认持仓，准备次日计划",
            "key_points": ["持仓结构", "次日预案"],
        })

        return plans

    def _gen_risk_reminder(
        self,
        config: PortfolioConfig,
        diag,
    ) -> List[str]:
        """生成风险提醒"""
        reminders = []
        phase = diag.emotion_phase.phase

        reminders.append(f"当前处于{phase}期，{diag.emotion_phase.operation_suggestion}")

        if phase == "高潮":
            reminders.append("情绪高潮随时可能退潮，严格控制新仓位")
        elif phase == "退潮":
            reminders.append("退潮期风险极大，建议空仓或极小仓位")

        reminders.append(f"单笔仓位不超过{config.single_position_limit}%")
        reminders.append(f"止损规则: {config.stop_loss_rule}")
        reminders.append(f"最大回撤限制: {config.max_drawdown_limit}%")

        if diag.fund_direction.fund_flow_score < 30:
            reminders.append("资金活跃度低，注意流动性风险")

        return reminders

    def _emotion_to_position(self, phase: str, max_pos: int) -> int:
        """情绪阶段映射到仓位"""
        ratios = {
            "冰点": 0.3,
            "修复": 0.8,
            "高潮": 0.4,
            "退潮": 0.0,
        }
        ratio = ratios.get(phase, 0.5)
        return int(max_pos * ratio)

    def _allocate_positions(
        self,
        config: PortfolioConfig,
        total_position: int,
    ) -> List[Dict]:
        """分配仓位"""
        positions = []
        for yingyou_name, ratio in config.yingyou_allocation.items():
            fp = registry.get(yingyou_name)
            if not fp:
                continue
            yingyou_position = int(total_position * ratio)
            positions.append({
                "yingyou": yingyou_name,
                "allocated_pct": yingyou_position,
                "max_single": min(config.single_position_limit, yingyou_position),
                "tactic": fp.classic_tactics[0]["name"] if fp.classic_tactics else "",
                "stop_loss": fp.stop_loss_rule,
            })
        return positions

    async def _gen_entry_plan(
        self,
        config: PortfolioConfig,
        diag,
        tickers: Optional[List[Dict[str, str]]] = None,
    ) -> List[Dict]:
        """生成入场计划"""
        entries = []

        for yingyou_name in config.yingyou_allocation:
            fp = registry.get(yingyou_name)
            if not fp:
                continue

            # 获取该游资当前最适用的战法
            best_tactic = fp.classic_tactics[0] if fp.classic_tactics else None

            entry = {
                "yingyou": yingyou_name,
                "tactic": best_tactic["name"] if best_tactic else "",
                "entry_method": fp.entry_timing.get("entry_method", ""),
                "position": f"{min(config.single_position_limit, int(config.max_position * config.yingyou_allocation[yingyou_name]))}%",
                "conditions": fp.entry_timing.get("signals", [])[:3],
            }
            entries.append(entry)

        return entries

    def _gen_exit_plan(self, config: PortfolioConfig, diag) -> List[Dict]:
        """生成出场计划"""
        return [
            {
                "trigger": "止盈",
                "rule": config.take_profit_rule,
                "action": "全部清仓或减半",
            },
            {
                "trigger": "止损",
                "rule": config.stop_loss_rule,
                "action": "无条件清仓，不犹豫",
            },
            {
                "trigger": "情绪退潮",
                "rule": f"{diag.emotion_phase.phase}转退潮",
                "action": "清仓或降至1成以内",
            },
        ]

    def _gen_emergency_plan(self, config: PortfolioConfig, diag) -> str:
        """生成应急方案"""
        return (
            f"若单日亏损超过{config.max_drawdown_limit//2}%，立即减仓至半仓; "
            f"若单月亏损接近{config.max_drawdown_limit}%，强制空仓休息; "
            "若持仓标的突发利空，集合竞价直接挂跌停价卖出"
        )

    def _gen_review_criteria(self, config: PortfolioConfig) -> List[str]:
        """生成复盘标准"""
        return [
            "今日是否遵守了计划?",
            f"止损执行是否果断?(规则: {config.stop_loss_rule})",
            "仓位控制是否合理?",
            "情绪周期判断是否准确?",
            "是否有计划外交易?",
            "今日最大感悟是什么?",
        ]

    def get_all_levels(self) -> List[str]:
        """获取所有等级"""
        return ["新手", "进阶", "高手"]

    def get_level_description(self, level: str) -> Dict:
        """获取等级描述"""
        config = self.factory.get_config(level)
        if not config:
            return {}
        return {
            "level": config.level,
            "yingyou": list(config.yingyou_allocation.keys()),
            "max_position": f"{config.max_position}%",
            "single_limit": f"{config.single_position_limit}%",
            "daily_trades": config.daily_trade_limit,
            "expected_return": config.expected_return_monthly,
            "max_drawdown": f"{config.max_drawdown_limit}%",
            "core_philosophy": config.core_philosophy[:100] + "...",
        }


# 全局引擎实例
portfolio_engine = PortfolioStrategyEngine()
