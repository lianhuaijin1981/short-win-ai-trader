"""预期分级评估模块 — 盘中看盘核心组件

对锚定标的进行预期分级评估，判定实际走势是否符合预期:
- 低于预期 — 实际弱于预判，需警惕转弱信号
- 符合预期 — 实际与预判一致，按计划执行
- 强于预期 — 实际强于预判，可适当乐观

触发条件和操作建议:
- 低于预期: 缩量高开低走/核按钮/炸板无回封 → 减仓/离场
- 符合预期: 量价正常/按剧本演绎 → 持仓观察
- 强于预期: 超预期连板/竞价抢筹/带动板块 → 加仓/锁仓

评估维度:
1. 竞价表现: 高开幅度 vs 预期
2. 开盘5分钟: 量能、承接力度
3. 盘中走势: 是否按剧本演绎
4. 板块配合: 跟风是否给力
"""

import asyncio
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional

from ...core.config import AppConfig
from ...core.exceptions import ModuleError
from ...core.logger import get_logger
from ...data_platform.data_models import (
    AnchorStock,
    ExpectationLevel,
    ExpectationEvaluation,
)

logger = get_logger("swat.m03.expectation_evaluator")


# ── 常量定义 ────────────────────────────────────────────

# 预期分级判定阈值
# 低于预期阈值
BELOW_OPEN_HIGH_MIN = 3.0       # 低于预期: 高开低于3%
BELOW_VOLUME_RATIO = 0.8        # 低于预期: 量比低于0.8
BELOW_DROP_PCT = -3.0           # 低于预期: 开盘后跌幅超3%

# 符合预期阈值
MEET_OPEN_HIGH_RANGE = (3.0, 7.0)   # 符合预期: 高开3-7%
MEET_VOLUME_RATIO_RANGE = (1.0, 3.0)  # 符合预期: 量比1-3

# 强于预期阈值
ABOVE_OPEN_HIGH_MIN = 7.0       # 强于预期: 高开≥7%
ABOVE_VOLUME_RATIO = 3.0        # 强于预期: 量比≥3
ABOVE_BOARD_THRESHOLD = 1       # 强于预期: 加速连板

# 时间节点
AUCTION_END_TIME = "09:25"      # 集合竞价结束
OPEN_5MIN_END = "09:35"         # 开盘5分钟
OPEN_30MIN_END = "10:00"        # 开盘30分钟


@dataclass
class ExpectationCriteria:
    """预期判定条件组"""
    open_high_pct: float = 0.0          # 高开幅度(%)
    volume_ratio: float = 0.0           # 量比
    high_5min_pct: float = 0.0          # 5分钟最高涨幅(%)
    current_pct: float = 0.0            # 当前涨幅(%)
    support_strength: str = ""          # 承接力度: 强/中/弱
    board_status: str = ""              # 涨停状态: 涨停/炸板/未涨停
    follower_count: int = 0             # 跟风股数量
    sector_avg_change: float = 0.0      # 板块平均涨幅


@dataclass
class ExpectationResult:
    """预期评估结果"""
    ticker: str = ""
    name: str = ""
    expectation: ExpectationLevel = ExpectationLevel.MEET
    score: float = 0.0                  # 预期分: 0-100
    criteria: Optional[ExpectationCriteria] = None
    reasons: List[str] = field(default_factory=list)
    operation: str = ""                 # 操作建议
    urgency: str = "normal"             # 紧急程度


class ExpectationEvaluator:
    """预期分级评估器

    对锚定标的的实际走势进行预期分级判定:
    - 低于预期: 需要减仓或离场
    - 符合预期: 按计划执行
    - 强于预期: 可以加仓或锁仓

    Attributes:
        config: 应用配置
        _evaluations: 评估结果缓存
    """

    def __init__(self, config: Optional[AppConfig] = None):
        """初始化预期分级评估器

        Args:
            config: 应用配置对象
        """
        self.config = config or AppConfig()
        self._evaluations: Dict[str, ExpectationResult] = {}
        logger.info("预期分级评估器初始化完成")

    # ==================== 核心公共接口 ====================

    async def evaluate_expectations(
        self,
        anchors: List[AnchorStock],
        real_time_data: Dict[str, Dict],
        sector_data: Optional[Dict[str, Dict]] = None,
    ) -> List[ExpectationResult]:
        """批量评估锚定标的是否符合预期 — 主入口

        Args:
            anchors: 锚定标的列表
            real_time_data: 实时数据 {ticker: {open_high, volume_ratio, high_5min, current, ...}}
            sector_data: 板块数据 {sector_name: {avg_change, limit_up_count}}

        Returns:
            List[ExpectationResult]: 各标的预期评估结果

        Raises:
            ModuleError: 评估过程发生严重错误
        """
        logger.info(f"========== 开始预期分级评估: {len(anchors)}只标的 ==========")

        try:
            results: List[ExpectationResult] = []

            for anchor in anchors:
                ticker = anchor.ticker
                if ticker not in real_time_data:
                    logger.warning(f"缺少{ticker}实时数据，跳过评估")
                    continue

                result = self._evaluate_single(
                    anchor=anchor,
                    rt_data=real_time_data[ticker],
                    sector_data=sector_data.get(anchor.anchor_type.value, {}) if sector_data else {},
                )
                results.append(result)
                self._evaluations[ticker] = result

                logger.info(
                    f"{anchor.name}({ticker}): {result.expectation.value} "
                    f"— {result.operation}"
                )

            # 更新标的预期
            self._update_anchor_expectations(anchors, results)

            logger.info(f"预期评估完成: 低于预期{sum(1 for r in results if r.expectation == ExpectationLevel.BELOW)}只, "
                        f"符合预期{sum(1 for r in results if r.expectation == ExpectationLevel.MEET)}只, "
                        f"强于预期{sum(1 for r in results if r.expectation == ExpectationLevel.ABOVE)}只")
            return results

        except Exception as e:
            logger.error(f"预期分级评估严重错误: {e}")
            raise ModuleError(f"预期评估失败: {e}")

    def get_expectation(self, ticker: str) -> Optional[ExpectationResult]:
        """获取指定标的的预期评估结果

        Args:
            ticker: 股票代码

        Returns:
            Optional[ExpectationResult]: 评估结果
        """
        return self._evaluations.get(ticker)

    def get_all_evaluations(self) -> Dict[str, ExpectationResult]:
        """获取所有评估结果

        Returns:
            Dict[str, ExpectationResult]: 全部评估
        """
        return self._evaluations.copy()

    # ==================== 单标的评估 ====================

    def _evaluate_single(
        self,
        anchor: AnchorStock,
        rt_data: Dict,
        sector_data: Dict,
    ) -> ExpectationResult:
        """评估单只标的是否符合预期

        综合考量竞价、开盘5分钟、盘中走势和板块配合。

        Args:
            anchor: 锚定标的
            rt_data: 实时数据
            sector_data: 板块数据

        Returns:
            ExpectationResult: 评估结果
        """
        ticker = anchor.ticker
        name = anchor.name

        # 构建判定条件
        criteria = ExpectationCriteria(
            open_high_pct=rt_data.get("open_high_pct", 0.0),
            volume_ratio=rt_data.get("volume_ratio", 0.0),
            high_5min_pct=rt_data.get("high_5min_pct", 0.0),
            current_pct=rt_data.get("change_pct", 0.0),
            support_strength=rt_data.get("support_strength", "中"),
            board_status=rt_data.get("board_status", "未涨停"),
            follower_count=rt_data.get("follower_count", 0),
            sector_avg_change=sector_data.get("avg_change", 0.0),
        )

        # 计算预期分数 (0-100)
        score = self._calculate_expectation_score(criteria, anchor)

        # 判定预期分级
        expectation, reasons = self._classify_expectation(score, criteria, anchor)

        # 生成操作建议
        operation = self._generate_operation_advice(expectation, criteria, anchor)

        # 紧急程度
        urgency = self._determine_urgency(expectation, criteria)

        return ExpectationResult(
            ticker=ticker,
            name=name,
            expectation=expectation,
            score=score,
            criteria=criteria,
            reasons=reasons,
            operation=operation,
            urgency=urgency,
        )

    def _calculate_expectation_score(
        self,
        criteria: ExpectationCriteria,
        anchor: AnchorStock,
    ) -> float:
        """计算预期评分 (0-100)

        综合多个维度计算实际表现与预期的匹配度。

        Args:
            criteria: 判定条件
            anchor: 锚定标的

        Returns:
            float: 预期评分
        """
        score = 50.0  # 基础分

        # 高开幅度评分 (±20分)
        open_high = criteria.open_high_pct
        if anchor.anchor_type.value == "市场总龙":
            # 总龙预期高开
            if open_high >= 5:
                score += 15
            elif open_high >= 3:
                score += 10
            elif open_high >= 1:
                score += 5
            elif open_high > 0:
                score += 0
            else:
                score -= 15
        else:
            # 其他标的
            if open_high >= 3:
                score += 10
            elif open_high >= 1:
                score += 5
            elif open_high > 0:
                score += 0
            elif open_high > -3:
                score -= 10
            else:
                score -= 20

        # 量比评分 (±15分)
        vol_ratio = criteria.volume_ratio
        if vol_ratio >= 2.0:
            score += 15
        elif vol_ratio >= 1.0:
            score += 10
        elif vol_ratio >= 0.5:
            score += 0
        else:
            score -= 15

        # 5分钟走势评分 (±20分)
        high_5m = criteria.high_5min_pct
        if high_5m >= 7:
            score += 20
        elif high_5m >= 3:
            score += 10
        elif high_5m >= 0:
            score += 0
        elif high_5m > -3:
            score -= 10
        else:
            score -= 20

        # 承接力度评分 (±15分)
        if criteria.support_strength == "强":
            score += 15
        elif criteria.support_strength == "中":
            score += 5
        elif criteria.support_strength == "弱":
            score -= 15

        # 涨停状态评分 (±15分)
        if criteria.board_status == "涨停":
            score += 15
        elif criteria.board_status == "炸板":
            score -= 10
        elif criteria.board_status == "回封":
            score += 10

        # 板块配合评分 (±15分)
        if criteria.follower_count >= 3:
            score += 15
        elif criteria.follower_count >= 1:
            score += 8
        elif criteria.sector_avg_change >= 2:
            score += 10
        elif criteria.sector_avg_change < 0:
            score -= 10

        return max(0, min(100, score))

    def _classify_expectation(
        self,
        score: float,
        criteria: ExpectationCriteria,
        anchor: AnchorStock,
    ) -> Tuple[ExpectationLevel, List[str]]:
        """根据评分判定预期分级

        Args:
            score: 预期评分
            criteria: 判定条件
            anchor: 锚定标的

        Returns:
            Tuple[ExpectationLevel, List[str]]: 预期分级和原因
        """
        reasons: List[str] = []

        # 低于预期判定
        if score < 40:
            expectation = ExpectationLevel.BELOW
            if criteria.open_high_pct < 0:
                reasons.append(f"低开{criteria.open_high_pct:.1f}%")
            elif criteria.open_high_pct < 2:
                reasons.append(f"高开不足({criteria.open_high_pct:.1f}%)")
            if criteria.volume_ratio < 0.8:
                reasons.append(f"量能不济(量比{criteria.volume_ratio:.1f})")
            if criteria.board_status == "炸板":
                reasons.append("炸板无回封")
            if criteria.support_strength == "弱":
                reasons.append("承接无力")
            if not reasons:
                reasons.append("综合评分低于40，整体表现疲软")

        # 强于预期判定
        elif score >= 75:
            expectation = ExpectationLevel.ABOVE
            if criteria.open_high_pct >= 7:
                reasons.append(f"大幅高开{criteria.open_high_pct:.1f}%")
            elif criteria.open_high_pct >= 5:
                reasons.append(f"强势高开{criteria.open_high_pct:.1f}%")
            if criteria.volume_ratio >= 3:
                reasons.append(f"巨量抢筹(量比{criteria.volume_ratio:.1f})")
            elif criteria.volume_ratio >= 2:
                reasons.append(f"放量上攻(量比{criteria.volume_ratio:.1f})")
            if criteria.board_status == "涨停":
                reasons.append("强势封板")
            if criteria.follower_count >= 3:
                reasons.append(f"带动{criteria.follower_count}只跟风涨停")
            if not reasons:
                reasons.append("综合评分75+，表现超预期")

        # 符合预期判定
        else:
            expectation = ExpectationLevel.MEET
            if 3 <= criteria.open_high_pct < 7:
                reasons.append(f"高开{criteria.open_high_pct:.1f}%符合预期")
            elif 1 <= criteria.open_high_pct < 3:
                reasons.append(f"小幅高开{criteria.open_high_pct:.1f}%")
            if 1 <= criteria.volume_ratio < 3:
                reasons.append(f"量能正常(量比{criteria.volume_ratio:.1f})")
            if criteria.support_strength in ("强", "中"):
                reasons.append(f"承接{criteria.support_strength}")
            if not reasons:
                reasons.append("走势正常，符合预期区间")

        return expectation, reasons

    def _generate_operation_advice(
        self,
        expectation: ExpectationLevel,
        criteria: ExpectationCriteria,
        anchor: AnchorStock,
    ) -> str:
        """生成操作建议

        根据预期分级和具体情况，给出针对性操作建议。

        Args:
            expectation: 预期分级
            criteria: 判定条件
            anchor: 锚定标的

        Returns:
            str: 操作建议文本
        """
        advice_parts: List[str] = []

        if expectation == ExpectationLevel.BELOW:
            advice_parts.append("[低于预期]")

            if anchor.anchor_type.value == "市场总龙":
                if criteria.board_status == "炸板":
                    advice_parts.append("总龙炸板——减仓一半，观察回封")
                elif criteria.open_high_pct < 0:
                    advice_parts.append("总龙低开——不低吸，等盘中反抽减")
                else:
                    advice_parts.append("总龙走弱——分批减仓")
            elif anchor.anchor_type.value == "先锋龙":
                advice_parts.append("先锋熄火——离场为主")
            elif anchor.anchor_type.value == "板块中军":
                advice_parts.append("中军走弱——减仓观望")
            else:
                advice_parts.append("走势不及预期——降低仓位")

            # 通用建议
            if criteria.volume_ratio < 0.5:
                advice_parts.append("量能极度萎缩，放弃幻想")
            if criteria.support_strength == "弱":
                advice_parts.append("无承接，及时止损")

        elif expectation == ExpectationLevel.MEET:
            advice_parts.append("[符合预期]")

            if anchor.anchor_type.value == "市场总龙":
                advice_parts.append("总龙正常——锁仓观察")
            elif anchor.anchor_type.value == "先锋龙":
                advice_parts.append("先锋正常——持股待涨")
            elif anchor.anchor_type.value == "板块中军":
                advice_parts.append("中军稳健——作为趋势锚定")
            else:
                advice_parts.append("走势正常——按计划执行")

            if criteria.board_status == "涨停":
                advice_parts.append("已涨停，观察封单量")

        elif expectation == ExpectationLevel.ABOVE:
            advice_parts.append("[强于预期]")

            if anchor.anchor_type.value == "市场总龙":
                advice_parts.append("总龙超预期——锁仓，龙头信仰")
            elif anchor.anchor_type.value == "先锋龙":
                advice_parts.append("先锋超预期——可适当加仓")
            elif anchor.anchor_type.value == "板块中军":
                advice_parts.append("中军超预期——板块有行情")
            else:
                advice_parts.append("走势强劲——持有或小幅加仓")

            if criteria.follower_count >= 5:
                advice_parts.append("强板块效应，享受溢价")
            if criteria.volume_ratio >= 5:
                advice_parts.append("爆量注意，观察持续性")

        return " | ".join(advice_parts)

    def _determine_urgency(
        self,
        expectation: ExpectationLevel,
        criteria: ExpectationCriteria,
    ) -> str:
        """判定紧急程度

        Args:
            expectation: 预期分级
            criteria: 判定条件

        Returns:
            str: 紧急程度
        """
        if expectation == ExpectationLevel.BELOW:
            if criteria.board_status == "炸板" or criteria.open_high_pct < -3:
                return "critical"
            return "high"
        elif expectation == ExpectationLevel.ABOVE:
            if criteria.board_status == "涨停" and criteria.volume_ratio > 5:
                return "high"  # 需要密切关注
            return "normal"
        return "normal"

    def _update_anchor_expectations(
        self,
        anchors: List[AnchorStock],
        results: List[ExpectationResult],
    ):
        """更新锚定标的的预期字段

        Args:
            anchors: 锚定标的列表
            results: 评估结果列表
        """
        result_map = {r.ticker: r for r in results}
        for anchor in anchors:
            if anchor.ticker in result_map:
                anchor.expectation = result_map[anchor.ticker].expectation

    # ==================== 便捷接口 ====================

    def quick_evaluate(
        self,
        ticker: str,
        open_high_pct: float,
        volume_ratio: float,
        current_pct: float,
        board_status: str = "未涨停",
    ) -> ExpectationLevel:
        """快速评估单只标的预期分级

        简化版评估，用于快速判定。

        Args:
            ticker: 股票代码
            open_high_pct: 高开幅度
            volume_ratio: 量比
            current_pct: 当前涨幅
            board_status: 涨停状态

        Returns:
            ExpectationLevel: 预期分级
        """
        score = 50.0

        # 高开评分
        if open_high_pct >= 5:
            score += 15
        elif open_high_pct >= 2:
            score += 5
        elif open_high_pct < 0:
            score -= 15

        # 量比评分
        if volume_ratio >= 2:
            score += 15
        elif volume_ratio < 0.5:
            score -= 15

        # 涨停状态
        if board_status == "涨停":
            score += 15
        elif board_status == "炸板":
            score -= 15

        # 当前走势
        if current_pct >= 7:
            score += 10
        elif current_pct < 0:
            score -= 10

        if score >= 75:
            return ExpectationLevel.ABOVE
        elif score < 40:
            return ExpectationLevel.BELOW
        return ExpectationLevel.MEET

    def clear_evaluations(self):
        """清空评估缓存"""
        self._evaluations.clear()
        logger.info("预期评估缓存已清空")
