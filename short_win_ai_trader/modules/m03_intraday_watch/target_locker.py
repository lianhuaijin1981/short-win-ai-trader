"""出手标的锁定器 — 盘中看盘核心组件

综合多维度数据，为超短选手智能锁定最佳出手标的:
- 锚定标的评分（身位/辨识度/带动性/溢价）
- 信号共振（多信号叠加优先）
- 生态位置（龙头/先锋/中军/跟风）
- 情绪周期适配（不同周期推荐不同标的）
- 资金主攻方向（跟随主力资金）

出手标的分级:
- S级: 多信号共振+龙头地位+情绪适配 → 重仓出击
- A级: 强信号+核心地位 → 正常仓位
- B级: 单信号+一般地位 → 轻仓试错
- C级: 弱信号 → 观察为主

出手时机判断:
- 竞价超预期 → 开盘跟随
- 分歧转一致 → 回封跟随
- 板块共振 → 前排龙头
- 情绪冰点 → 试错新龙
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

from ...core.config import AppConfig
from ...core.exceptions import ModuleError
from ...core.logger import get_logger
from ...data_platform.data_models import (
    AnchorStock,
    AnchorType,
    EmotionCycle,
    ExpectationLevel,
    LimitUpStock,
    ThemeData,
)

logger = get_logger("swat.m03.target_locker")


# ── 常量定义 ────────────────────────────────────────────

# 出手标的分级阈值
GRADE_S_MIN_SCORE = 85.0          # S级最低分
GRADE_A_MIN_SCORE = 70.0          # A级最低分
GRADE_B_MIN_SCORE = 55.0          # B级最低分

# 信号共振加分
SIGNAL_RESONANCE_BONUS = 15.0     # 多信号共振加分
SIGNAL_SINGLE_BONUS = 8.0         # 单信号加分

# 情绪周期适配加分
EMOTION_MATCH_BONUS = 10.0        # 情绪周期适配加分
EMOTION_MISMATCH_PENALTY = -15.0  # 情绪周期不匹配扣分

# 资金方向加分
FUND_DIRECTION_BONUS = 10.0       # 资金主攻方向加分

# 仓位建议
POSITION_S = "50-70%"             # S级仓位
POSITION_A = "30-50%"             # A级仓位
POSITION_B = "10-30%"             # B级仓位
POSITION_C = "观察"                # C级仓位


class TargetGrade(str, Enum):
    """出手标的分级"""
    S = "S级"
    A = "A级"
    B = "B级"
    C = "C级"


class EntryTiming(str, Enum):
    """出手时机"""
    AUCTION_FOLLOW = "竞价跟随"
    OPEN_FOLLOW = "开盘跟随"
    DIVERGENCE_LOW = "分歧低吸"
    RESEAL_FOLLOW = "回封跟随"
    BREAKOUT_FOLLOW = "突破跟随"
    ICE_TRIAL = "冰点试错"
    WAIT = "等待确认"


@dataclass
class TargetScore:
    """出手标的评分明细"""
    ticker: str = ""
    name: str = ""
    anchor_score: float = 0.0         # 锚定评分(0-100)
    signal_bonus: float = 0.0         # 信号加分
    emotion_bonus: float = 0.0        # 情绪适配加分
    fund_bonus: float = 0.0           # 资金方向加分
    ecology_bonus: float = 0.0        # 生态位置加分
    total_score: float = 0.0          # 总分
    grade: TargetGrade = TargetGrade.C
    matched_signals: List[str] = field(default_factory=list)
    entry_timing: EntryTiming = EntryTiming.WAIT
    position_suggestion: str = ""
    action_plan: str = ""


@dataclass
class LockedTarget:
    """锁定的出手标的"""
    ticker: str = ""
    name: str = ""
    grade: TargetGrade = TargetGrade.C
    total_score: float = 0.0
    anchor_type: str = ""
    theme: str = ""
    expectation: str = ""
    entry_timing: EntryTiming = EntryTiming.WAIT
    position_suggestion: str = ""
    action_plan: str = ""
    risk_warning: str = ""
    score_detail: Optional[TargetScore] = None
    timestamp: Optional[datetime] = None


@dataclass
class TargetLockReport:
    """出手标的锁定报告"""
    timestamp: Optional[datetime] = None
    locked_targets: List[LockedTarget] = field(default_factory=list)
    s_grade_count: int = 0
    a_grade_count: int = 0
    b_grade_count: int = 0
    c_grade_count: int = 0
    market_mood: str = ""
    emotion_cycle: str = ""
    overall_strategy: str = ""
    summary_text: str = ""


class TargetLocker:
    """出手标的锁定器
    
    综合多维度数据，智能锁定最佳出手标的。
    
    Attributes:
        config: 应用配置
        _emotion_cycle: 当前情绪周期
    """
    
    def __init__(self, config: Optional[AppConfig] = None):
        """初始化出手标的锁定器
        
        Args:
            config: 应用配置对象
        """
        self.config = config or AppConfig()
        self._emotion_cycle = EmotionCycle.CHAOS
        self._market_mood = "正常"
        logger.info("出手标的锁定器初始化完成")
    
    # ==================== 核心公共接口 ====================
    
    async def lock_targets(
        self,
        anchors: List[AnchorStock],
        limit_up_stocks: List[LimitUpStock],
        themes: List[ThemeData],
        real_time_data: Dict[str, Dict],
        signal_summary: Optional[Dict] = None,
        fund_report: Optional[Dict] = None,
        emotion_cycle: Optional[EmotionCycle] = None,
        market_mood: str = "正常",
    ) -> TargetLockReport:
        """出手标的锁定主入口
        
        执行完整锁定流程: 评分计算 → 信号共振 → 情绪适配 → 分级排序
        
        Args:
            anchors: 锚定标的列表
            limit_up_stocks: 涨停股列表
            themes: 题材列表
            real_time_data: 实时数据
            signal_summary: 信号汇总
            fund_report: 资金流向报告
            emotion_cycle: 情绪周期
            market_mood: 市场情绪
            
        Returns:
            TargetLockReport: 出手标的锁定报告
            
        Raises:
            ModuleError: 锁定过程发生严重错误
        """
        logger.info("========== 开始出手标的锁定 ==========")
        
        try:
            # 更新情绪周期
            if emotion_cycle:
                self._emotion_cycle = emotion_cycle
            self._market_mood = market_mood
            
            # Step 1: 计算各标的综合评分
            logger.info("[Step 1/4] 计算综合评分...")
            scores = self._calculate_scores(
                anchors, real_time_data, signal_summary, fund_report
            )
            
            # Step 2: 判定出手时机
            logger.info("[Step 2/4] 判定出手时机...")
            scores = self._determine_entry_timing(scores, real_time_data)
            
            # Step 3: 分级排序
            logger.info("[Step 3/4] 分级排序...")
            scores = self._grade_and_sort(scores)
            
            # Step 4: 生成锁定报告
            logger.info("[Step 4/4] 生成锁定报告...")
            report = self._generate_report(scores, anchors, limit_up_stocks)
            
            logger.info(
                f"出手标的锁定完成: S级{report.s_grade_count}只, "
                f"A级{report.a_grade_count}只, B级{report.b_grade_count}只"
            )
            return report
            
        except Exception as e:
            logger.error(f"出手标的锁定严重错误: {e}")
            raise ModuleError(f"出手标的锁定失败: {e}")
    
    def set_emotion_cycle(self, cycle: EmotionCycle):
        """设置当前情绪周期
        
        Args:
            cycle: 情绪周期
        """
        self._emotion_cycle = cycle
        logger.info(f"情绪周期已更新: {cycle.value}")
    
    # ==================== 步骤1: 综合评分 ====================
    
    def _calculate_scores(
        self,
        anchors: List[AnchorStock],
        real_time_data: Dict[str, Dict],
        signal_summary: Optional[Dict] = None,
        fund_report: Optional[Dict] = None,
    ) -> List[TargetScore]:
        """计算各标的综合评分
        
        Args:
            anchors: 锚定标的
            real_time_data: 实时数据
            signal_summary: 信号汇总
            fund_report: 资金流向报告
            
        Returns:
            List[TargetScore]: 评分列表
        """
        scores: List[TargetScore] = []
        
        # 提取信号标的
        signal_tickers: Dict[str, List[str]] = {}
        if signal_summary:
            for sig_type, sig_list in signal_summary.get("signals", {}).items():
                for sig in sig_list:
                    ticker = sig.get("ticker", "")
                    if ticker:
                        if ticker not in signal_tickers:
                            signal_tickers[ticker] = []
                        signal_tickers[ticker].append(sig_type)
        
        # 提取资金主攻方向
        fund_directions = set()
        if fund_report:
            first_dir = fund_report.get("first_direction", "")
            if first_dir:
                fund_directions.add(first_dir)
            second_dir = fund_report.get("second_direction", "")
            if second_dir:
                fund_directions.add(second_dir)
        
        for anchor in anchors:
            ticker = anchor.ticker
            name = anchor.name
            
            # 基础分: 锚定评分
            anchor_score = anchor.score
            
            # 信号加分
            signal_bonus = 0.0
            matched_signals = signal_tickers.get(ticker, [])
            if len(matched_signals) >= 2:
                signal_bonus = SIGNAL_RESONANCE_BONUS  # 多信号共振
            elif len(matched_signals) == 1:
                signal_bonus = SIGNAL_SINGLE_BONUS
            
            # 情绪周期适配加分
            emotion_bonus = self._calculate_emotion_bonus(anchor)
            
            # 资金方向加分
            fund_bonus = 0.0
            anchor_theme = ""
            for theme_data in []:  # 需要从外部传入themes
                pass
            # 简化处理: 如果锚定标的是龙头，默认有资金关注
            if anchor.anchor_type in (AnchorType.TOTAL_DRAGON, AnchorType.BRANCH_DRAGON):
                fund_bonus = FUND_DIRECTION_BONUS * 0.8
            elif anchor.anchor_type == AnchorType.PIONEER:
                fund_bonus = FUND_DIRECTION_BONUS * 0.6
            
            # 生态位置加分
            ecology_bonus = self._calculate_ecology_bonus(anchor)
            
            # 实时数据加分
            rt_bonus = self._calculate_realtime_bonus(ticker, real_time_data)
            
            # 总分
            total_score = (
                anchor_score
                + signal_bonus
                + emotion_bonus
                + fund_bonus
                + ecology_bonus
                + rt_bonus
            )
            total_score = max(0, min(100, total_score))
            
            score = TargetScore(
                ticker=ticker,
                name=name,
                anchor_score=anchor_score,
                signal_bonus=signal_bonus,
                emotion_bonus=emotion_bonus,
                fund_bonus=fund_bonus,
                ecology_bonus=ecology_bonus,
                total_score=total_score,
                matched_signals=matched_signals,
            )
            scores.append(score)
        
        return scores
    
    def _calculate_emotion_bonus(self, anchor: AnchorStock) -> float:
        """计算情绪周期适配加分
        
        不同情绪周期适合不同类型的标的:
        - 启动期: 先锋龙
        - 发酵期: 分支龙头
        - 高潮期: 市场总龙
        - 分歧期: 板块中军（抗跌）
        - 退潮期: 无（不操作）
        - 混沌期: 观察
        
        Args:
            anchor: 锚定标的
            
        Returns:
            float: 情绪适配加分
        """
        cycle = self._emotion_cycle
        anchor_type = anchor.anchor_type
        
        # 退潮期: 全部扣分
        if cycle == EmotionCycle.RETREAT:
            return EMOTION_MISMATCH_PENALTY
        
        # 启动期: 先锋龙加分
        if cycle == EmotionCycle.START:
            if anchor_type == AnchorType.PIONEER:
                return EMOTION_MATCH_BONUS
            elif anchor_type == AnchorType.TOTAL_DRAGON:
                return EMOTION_MATCH_BONUS * 0.5
        
        # 发酵期: 分支龙头加分
        elif cycle == EmotionCycle.FERMENT:
            if anchor_type == AnchorType.BRANCH_DRAGON:
                return EMOTION_MATCH_BONUS
            elif anchor_type == AnchorType.PIONEER:
                return EMOTION_MATCH_BONUS * 0.7
        
        # 高潮期: 市场总龙加分
        elif cycle == EmotionCycle.PEAK:
            if anchor_type == AnchorType.TOTAL_DRAGON:
                return EMOTION_MATCH_BONUS
            elif anchor_type == AnchorType.BRANCH_DRAGON:
                return EMOTION_MATCH_BONUS * 0.5
            else:
                return EMOTION_MISMATCH_PENALTY * 0.5  # 高潮期跟风风险大
        
        # 分歧期: 中军抗跌
        elif cycle == EmotionCycle.DIVERGE:
            if anchor_type == AnchorType.SECTOR_CORE:
                return EMOTION_MATCH_BONUS * 0.8
            elif anchor_type == AnchorType.TOTAL_DRAGON:
                return EMOTION_MATCH_BONUS * 0.5
        
        # 混沌期: 不加分不扣分
        return 0.0
    
    def _calculate_ecology_bonus(self, anchor: AnchorStock) -> float:
        """计算生态位置加分
        
        Args:
            anchor: 锚定标的
            
        Returns:
            float: 生态位置加分
        """
        anchor_type = anchor.anchor_type
        
        if anchor_type == AnchorType.TOTAL_DRAGON:
            return 15.0
        elif anchor_type == AnchorType.BRANCH_DRAGON:
            return 10.0
        elif anchor_type == AnchorType.PIONEER:
            return 8.0
        elif anchor_type == AnchorType.SECTOR_CORE:
            return 5.0
        return 0.0
    
    def _calculate_realtime_bonus(
        self, 
        ticker: str, 
        real_time_data: Dict[str, Dict]
    ) -> float:
        """计算实时数据加分
        
        Args:
            ticker: 股票代码
            real_time_data: 实时数据
            
        Returns:
            float: 实时数据加分
        """
        if ticker not in real_time_data:
            return 0.0
        
        rt = real_time_data[ticker]
        bonus = 0.0
        
        # 超预期加分
        change_pct = rt.get("change_pct", 0)
        vol_ratio = rt.get("volume_ratio", 0)
        board_status = rt.get("board_status", "未涨停")
        
        if board_status == "涨停":
            bonus += 10.0
        elif board_status == "回封":
            bonus += 8.0
        elif board_status == "炸板":
            bonus -= 10.0
        
        if change_pct >= 7:
            bonus += 5.0
        elif change_pct >= 3:
            bonus += 3.0
        elif change_pct < -3:
            bonus -= 5.0
        
        if vol_ratio >= 3:
            bonus += 3.0
        elif vol_ratio >= 2:
            bonus += 2.0
        elif vol_ratio < 0.5:
            bonus -= 3.0
        
        return max(-15, min(15, bonus))
    
    # ==================== 步骤2: 出手时机判定 ====================
    
    def _determine_entry_timing(
        self,
        scores: List[TargetScore],
        real_time_data: Dict[str, Dict],
    ) -> List[TargetScore]:
        """判定出手时机
        
        Args:
            scores: 评分列表
            real_time_data: 实时数据
            
        Returns:
            List[TargetScore]: 更新后的评分列表
        """
        for score in scores:
            ticker = score.ticker
            rt = real_time_data.get(ticker, {})
            
            open_high = rt.get("open_high_pct", 0)
            vol_ratio = rt.get("volume_ratio", 0)
            board_status = rt.get("board_status", "未涨停")
            change_pct = rt.get("change_pct", 0)
            
            # 竞价超预期 → 竞价/开盘跟随
            if open_high >= 5 and vol_ratio >= 2:
                score.entry_timing = EntryTiming.AUCTION_FOLLOW
            
            # 回封 → 回封跟随
            elif board_status == "回封":
                score.entry_timing = EntryTiming.RESEAL_FOLLOW
            
            # 炸板后低吸 → 分歧低吸
            elif board_status == "炸板" and score.total_score >= 60:
                score.entry_timing = EntryTiming.DIVERGENCE_LOW
            
            # 放量突破 → 突破跟随
            elif vol_ratio >= 2.5 and change_pct >= 3:
                score.entry_timing = EntryTiming.BREAKOUT_FOLLOW
            
            # 冰点期 → 冰点试错
            elif self._market_mood == "冰点" and score.total_score >= 50:
                score.entry_timing = EntryTiming.ICE_TRIAL
            
            # 开盘正常 → 开盘跟随
            elif 0 < open_high < 5 and vol_ratio >= 1:
                score.entry_timing = EntryTiming.OPEN_FOLLOW
            
            else:
                score.entry_timing = EntryTiming.WAIT
        
        return scores
    
    # ==================== 步骤3: 分级排序 ====================
    
    def _grade_and_sort(self, scores: List[TargetScore]) -> List[TargetScore]:
        """分级并排序
        
        Args:
            scores: 评分列表
            
        Returns:
            List[TargetScore]: 分级排序后的列表
        """
        for score in scores:
            if score.total_score >= GRADE_S_MIN_SCORE:
                score.grade = TargetGrade.S
                score.position_suggestion = POSITION_S
            elif score.total_score >= GRADE_A_MIN_SCORE:
                score.grade = TargetGrade.A
                score.position_suggestion = POSITION_A
            elif score.total_score >= GRADE_B_MIN_SCORE:
                score.grade = TargetGrade.B
                score.position_suggestion = POSITION_B
            else:
                score.grade = TargetGrade.C
                score.position_suggestion = POSITION_C
        
        # 按总分降序
        scores.sort(key=lambda s: s.total_score, reverse=True)
        
        return scores
    
    # ==================== 步骤4: 生成报告 ====================
    
    def _generate_report(
        self,
        scores: List[TargetScore],
        anchors: List[AnchorStock],
        limit_up_stocks: List[LimitUpStock],
    ) -> TargetLockReport:
        """生成出手标的锁定报告
        
        Args:
            scores: 评分列表
            anchors: 锚定标的
            limit_up_stocks: 涨停股
            
        Returns:
            TargetLockReport: 锁定报告
        """
        now = datetime.now()
        
        # 构建锚定映射
        anchor_map = {a.ticker: a for a in anchors}
        
        # 统计分级
        s_count = sum(1 for s in scores if s.grade == TargetGrade.S)
        a_count = sum(1 for s in scores if s.grade == TargetGrade.A)
        b_count = sum(1 for s in scores if s.grade == TargetGrade.B)
        c_count = sum(1 for s in scores if s.grade == TargetGrade.C)
        
        # 生成锁定标的
        locked_targets: List[LockedTarget] = []
        for score in scores:
            anchor = anchor_map.get(score.ticker)
            
            # 生成操作计划
            action_plan = self._generate_action_plan(score, anchor)
            
            # 生成风险提示
            risk_warning = self._generate_risk_warning(score, anchor)
            
            locked = LockedTarget(
                ticker=score.ticker,
                name=score.name,
                grade=score.grade,
                total_score=score.total_score,
                anchor_type=anchor.anchor_type.value if anchor else "",
                theme=anchor.theme if hasattr(anchor, 'theme') else "",
                expectation=anchor.expectation.value if anchor else "",
                entry_timing=score.entry_timing,
                position_suggestion=score.position_suggestion,
                action_plan=action_plan,
                risk_warning=risk_warning,
                score_detail=score,
                timestamp=now,
            )
            locked_targets.append(locked)
        
        # 生成整体策略
        overall_strategy = self._generate_overall_strategy(
            s_count, a_count, b_count, scores
        )
        
        # 生成摘要
        parts: List[str] = []
        parts.append(f"=== 出手标的锁定 [{now.strftime('%H:%M')}] ===")
        parts.append(f"市场情绪: {self._market_mood}")
        parts.append(f"情绪周期: {self._emotion_cycle.value}")
        parts.append(f"分级: S级{s_count}只, A级{a_count}只, B级{b_count}只, C级{c_count}只")
        
        if s_count > 0:
            s_targets = [t for t in locked_targets if t.grade == TargetGrade.S]
            parts.append(f"🔥 S级标的: {', '.join(t.name for t in s_targets[:3])}")
        
        if a_count > 0:
            a_targets = [t for t in locked_targets if t.grade == TargetGrade.A]
            parts.append(f"⭐ A级标的: {', '.join(t.name for t in a_targets[:3])}")
        
        parts.append(f"整体策略: {overall_strategy}")
        
        return TargetLockReport(
            timestamp=now,
            locked_targets=locked_targets,
            s_grade_count=s_count,
            a_grade_count=a_count,
            b_grade_count=b_count,
            c_grade_count=c_count,
            market_mood=self._market_mood,
            emotion_cycle=self._emotion_cycle.value,
            overall_strategy=overall_strategy,
            summary_text="\n".join(parts),
        )
    
    def _generate_action_plan(
        self, 
        score: TargetScore, 
        anchor: Optional[AnchorStock]
    ) -> str:
        """生成操作计划
        
        Args:
            score: 评分
            anchor: 锚定标的
            
        Returns:
            str: 操作计划
        """
        parts: List[str] = []
        
        # 根据分级
        if score.grade == TargetGrade.S:
            parts.append(f"[{score.grade.value}] 重仓出击")
        elif score.grade == TargetGrade.A:
            parts.append(f"[{score.grade.value}] 正常仓位")
        elif score.grade == TargetGrade.B:
            parts.append(f"[{score.grade.value}] 轻仓试错")
        else:
            parts.append(f"[{score.grade.value}] 观察为主")
        
        # 根据时机
        timing_advice = {
            EntryTiming.AUCTION_FOLLOW: "竞价/开盘直接跟随",
            EntryTiming.OPEN_FOLLOW: "开盘观察5分钟后跟随",
            EntryTiming.DIVERGENCE_LOW: "分歧时低吸，不追高",
            EntryTiming.RESEAL_FOLLOW: "回封确认时跟随",
            EntryTiming.BREAKOUT_FOLLOW: "放量突破时跟随",
            EntryTiming.ICE_TRIAL: "冰点试错，小仓位",
            EntryTiming.WAIT: "等待确定性信号",
        }
        parts.append(timing_advice.get(score.entry_timing, "等待确认"))
        
        # 仓位建议
        parts.append(f"仓位: {score.position_suggestion}")
        
        # 信号共振
        if len(score.matched_signals) >= 2:
            parts.append(f"多信号共振: {', '.join(score.matched_signals)}")
        
        return " | ".join(parts)
    
    def _generate_risk_warning(
        self, 
        score: TargetScore, 
        anchor: Optional[AnchorStock]
    ) -> str:
        """生成风险提示
        
        Args:
            score: 评分
            anchor: 锚定标的
            
        Returns:
            str: 风险提示
        """
        warnings: List[str] = []
        
        if anchor:
            if anchor.expectation == ExpectationLevel.BELOW:
                warnings.append("低于预期，需谨慎")
            
            if anchor.anchor_type == AnchorType.TOTAL_DRAGON:
                warnings.append("总龙高位，注意断板风险")
        
        if score.total_score < 60:
            warnings.append("评分偏低，确定性不足")
        
        if self._emotion_cycle == EmotionCycle.RETREAT:
            warnings.append("退潮期，整体风险偏高")
        
        if self._market_mood == "冰点":
            warnings.append("情绪冰点，注意控制仓位")
        
        return "; ".join(warnings) if warnings else "无明显风险"
    
    def _generate_overall_strategy(
        self,
        s_count: int,
        a_count: int,
        b_count: int,
        scores: List[TargetScore],
    ) -> str:
        """生成整体策略
        
        Args:
            s_count: S级数量
            a_count: A级数量
            b_count: B级数量
            scores: 评分列表
            
        Returns:
            str: 整体策略
        """
        if self._emotion_cycle == EmotionCycle.RETREAT:
            return "退潮期，管住手，不操作或极轻仓试错"
        
        if self._market_mood == "冰点":
            return "情绪冰点，小仓位试错新方向，等待冰点修复"
        
        if s_count >= 2:
            return "多只S级标的，可积极操作，优先S级龙头"
        elif s_count == 1:
            return "有S级标的，重点出击，配合A级标的分散风险"
        elif a_count >= 2:
            return "无S级但有A级，正常仓位操作，选择确定性最高的"
        elif a_count == 1:
            return "仅1只A级，谨慎操作，控制仓位"
        elif b_count >= 2:
            return "仅B级标的，轻仓试错，快进快出"
        else:
            return "无优质标的，观望为主，等待更好机会"