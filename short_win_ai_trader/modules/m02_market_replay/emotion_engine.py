"""情绪周期研判引擎 — 全量化市场情绪周期识别与诊断

基于多因子模型，将市场情绪划分为标准化六段周期:
混沌期 → 启动期 → 发酵期 → 高潮期 → 分歧期 → 退潮期

核心功能:
- 多因子情绪量化指标计算
- 情绪周期自动研判（无人工主观判断）
- 情绪阶段-仓位自动匹配
- 适配交易模式推荐
"""

import math
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Tuple

from ...core.config import AppConfig
from ...core.exceptions import ModuleError
from ...core.logger import get_logger
from ...data_platform.data_models import (
    DragonBond,
    EmotionCycle,
    EmotionDiagnosis,
    EmotionIndicators,
    EmotionTrend,
    LimitUpStock,
    MarketSnapshot,
    ThemeData,
)

logger = get_logger("swat.m02.emotion_engine")


# ==================== 情绪-仓位-模式匹配表 ====================

CYCLE_CONFIG: Dict[EmotionCycle, Dict] = {
    EmotionCycle.CHAOS: {
        "position_limit": 20,           # 1-2成
        "adapted_mode": "低位首板、低位潜伏",
        "core_principle": "少出手、不接力、轻仓试错",
        "description": "市场情绪低迷，涨跌无序，题材快速轮动无持续性",
        "key_features": ["涨跌家数比<0.8", "涨停数<30", "最高连板<=2", "题材一日游"],
    },
    EmotionCycle.START: {
        "position_limit": 40,           # 3-4成
        "adapted_mode": "主线龙头先手、分歧低吸",
        "core_principle": "择优布局、建立底仓、逐步加仓",
        "description": "市场出现企稳信号，新题材开始活跃，试错资金入场",
        "key_features": ["涨跌家数比>1.2", "出现新题材首板", "连板高度突破3板", "量能温和放大"],
    },
    EmotionCycle.FERMENT: {
        "position_limit": 60,           # 5-6成
        "adapted_mode": "半路、低吸核心人气标",
        "core_principle": "顺势加仓、持有核心、放弃杂毛",
        "description": "主线题材得到市场认可，资金持续流入，赚钱效应扩散",
        "key_features": ["主线题材涨停数>10", "连板梯队完整", "龙头溢价明显", "量能持续放大"],
    },
    EmotionCycle.PEAK: {
        "position_limit": 30,           # 3成以下
        "adapted_mode": "核心龙头止盈、不追新标的",
        "core_principle": "逢高兑现、严控仓位、防范分歧",
        "description": "市场情绪达到顶峰，全线普涨，但已出现过热信号",
        "key_features": ["涨停数>80", "炸板率<15%", "普涨格局", "缩量加速", "情绪指标超买"],
    },
    EmotionCycle.DIVERGE: {
        "position_limit": 30,           # 2-3成
        "adapted_mode": "龙头首阴、分歧低吸",
        "core_principle": "谨慎博弈、快进快出、严格止损",
        "description": "强势股开始分化，后排标的掉队，亏钱效应初现",
        "key_features": ["炸板率>30%", "跌停数增加", "大面股增多", "龙头分歧开板", "跟风股先跌"],
    },
    EmotionCycle.RETREAT: {
        "position_limit": 10,           # 0-1成
        "adapted_mode": "停止高位交易、规避所有杂毛",
        "core_principle": "防守为主、优先避险、等待新周期",
        "description": "情绪全面退潮，跌停增多，强势股补跌，资金避险情绪浓厚",
        "key_features": ["跌停数>15", "连板高度降至2", "昨日涨停今日跌停", "量能萎缩", "全A下跌"],
    },
}


# ==================== 周期判定阈值 ====================

CYCLE_THRESHOLDS = {
    "retreat": {
        "limit_down_count": 15,
        "explode_rate": 50.0,
        "up_down_ratio": 0.3,
        "max_consecutive_boards": 2,
        "break_rate": 60.0,
    },
    "peak": {
        "limit_up_count": 80,
        "explode_rate": 15.0,
        "up_down_ratio": 3.0,
        "max_consecutive_boards": 8,
        "profit_effect": 80.0,
    },
    "diverge": {
        "explode_rate": 30.0,
        "limit_down_count": 5,
        "break_rate": 40.0,
        "up_down_ratio": 1.0,
    },
    "ferment": {
        "limit_up_count": 40,
        "up_down_ratio": 1.5,
        "promotion_rate": 50.0,
        "max_consecutive_boards": 5,
    },
    "start": {
        "up_down_ratio": 1.2,
        "limit_up_count": 25,
        "max_consecutive_boards": 3,
        "volume_change": 10.0,
    },
}


class EmotionEngine:
    """情绪周期研判引擎

    基于多因子量化模型，自动研判当前市场情绪所处周期阶段。
    支持情绪趋势分析、动态权重调整和极端值预警。

    Attributes:
        config: 应用配置
        emotion_weights: 四大因子权重（大盘/连板/资金/题材）
        emotion_history: 情绪历史数据缓存（用于趋势分析）
    """

    def __init__(self, config: AppConfig):
        """初始化情绪引擎

        Args:
            config: 应用配置对象
        """
        self.config = config
        self.emotion_weights = config.emotion_cycle.default_weights
        # 最近一次市场快照缓存（用于周期判定中引用原始市场数据）
        self._last_snapshot: Optional[MarketSnapshot] = None
        # 情绪历史记录: [(date, score, cycle), ...]
        self._emotion_history: List[Tuple[date, float, EmotionCycle]] = []
        # 动态权重调整系数
        self._weight_adjustments: Dict[str, float] = {
            "market": 1.0,
            "board": 1.0,
            "fund": 1.0,
            "theme": 1.0,
        }

        logger.info(
            "情绪周期研判引擎初始化完成",
            weights=self.emotion_weights,
        )

    def calculate_emotion_indicators(
        self,
        market_snap: MarketSnapshot,
        limit_up_stocks: List[LimitUpStock],
        themes: List[ThemeData],
        dragon_bonds: List[DragonBond],
    ) -> EmotionIndicators:
        """计算情绪量化指标

        从市场快照、涨停股、题材和龙虎榜数据中，
        提取14项核心情绪量化指标。

        Args:
            market_snap: 市场快照数据
            limit_up_stocks: 涨停股列表
            themes: 题材数据列表
            dragon_bonds: 龙虎榜数据列表

        Returns:
            EmotionIndicators 情绪量化指标对象

        Raises:
            ModuleError: 计算过程发生错误
        """
        try:
            logger.info("开始计算情绪量化指标...")

            # 1. 大盘指标计算
            up_down_ratio = self._calc_up_down_ratio(market_snap)
            explode_rate = market_snap.explode_rate
            profit_effect = self._calc_profit_effect(market_snap)
            volume_change = market_snap.volume_change_pct

            # 2. 连板指标计算
            max_boards, promotion_rate, break_rate = self._calc_board_indicators(
                limit_up_stocks
            )
            dragon_premium = self._calc_dragon_premium(limit_up_stocks)

            # 3. 资金指标计算
            main_inflow_ratio = self._calc_main_inflow(market_snap)
            yingyou_activity = self._calc_yingyou_activity(dragon_bonds)
            northbound_flow = self._calc_northbound_flow(market_snap)

            # 4. 题材指标计算
            theme_strength = self._calc_theme_strength(themes)
            sector_linkage = self._calc_sector_linkage(themes)
            theme_sustainability = self._calc_theme_sustainability(themes)

            # 缓存快照供周期判定使用
            self._last_snapshot = market_snap

            indicators = EmotionIndicators(
                up_down_ratio=round(up_down_ratio, 2),
                explode_rate=round(explode_rate, 2),
                profit_effect=round(profit_effect, 2),
                volume_change=round(volume_change, 2),
                max_consecutive_boards=max_boards,
                promotion_rate=round(promotion_rate, 2),
                break_rate=round(break_rate, 2),
                dragon_premium=round(dragon_premium, 2),
                main_inflow_ratio=round(main_inflow_ratio, 2),
                yingyou_activity=round(yingyou_activity, 2),
                northbound_flow=round(northbound_flow, 2),
                theme_strength=round(theme_strength, 2),
                sector_linkage=round(sector_linkage, 2),
                theme_sustainability=round(theme_sustainability, 2),
            )

            logger.info(
                "情绪指标计算完成",
                up_down_ratio=indicators.up_down_ratio,
                max_boards=indicators.max_consecutive_boards,
                explode_rate=indicators.explode_rate,
                profit_effect=indicators.profit_effect,
            )

            return indicators

        except Exception as e:
            logger.error(f"情绪指标计算错误: {e}")
            raise ModuleError(f"情绪指标计算失败: {e}")

    def diagnose_emotion_cycle(self, indicators: EmotionIndicators) -> EmotionDiagnosis:
        """情绪周期研判 — 六段周期自动判定

        基于量化指标，通过多因子加权判定当前情绪所处周期阶段。
        判定顺序: 退潮期 → 高潮期 → 分歧期 → 发酵期 → 启动期 → 混沌期
        （从极端状态到一般状态依次判断）

        Args:
            indicators: 情绪量化指标

        Returns:
            EmotionDiagnosis 情绪周期诊断结果
        """
        logger.info("开始情绪周期研判...")

        # 各周期得分计算
        cycle_scores: Dict[EmotionCycle, float] = {}
        reasons_map: Dict[EmotionCycle, List[str]] = {}

        # 退潮期判定
        score_retreat, reasons_retreat = self._score_retreat(indicators)
        cycle_scores[EmotionCycle.RETREAT] = score_retreat
        reasons_map[EmotionCycle.RETREAT] = reasons_retreat

        # 高潮期判定
        score_peak, reasons_peak = self._score_peak(indicators)
        cycle_scores[EmotionCycle.PEAK] = score_peak
        reasons_map[EmotionCycle.PEAK] = reasons_peak

        # 分歧期判定
        score_diverge, reasons_diverge = self._score_diverge(indicators)
        cycle_scores[EmotionCycle.DIVERGE] = score_diverge
        reasons_map[EmotionCycle.DIVERGE] = reasons_diverge

        # 发酵期判定
        score_ferment, reasons_ferment = self._score_ferment(indicators)
        cycle_scores[EmotionCycle.FERMENT] = score_ferment
        reasons_map[EmotionCycle.FERMENT] = reasons_ferment

        # 启动期判定
        score_start, reasons_start = self._score_start(indicators)
        cycle_scores[EmotionCycle.START] = score_start
        reasons_map[EmotionCycle.START] = reasons_start

        # 混沌期（默认兜底）
        score_chaos = max(0.0, 1.0 - max(cycle_scores.values()))
        cycle_scores[EmotionCycle.CHAOS] = score_chaos
        reasons_map[EmotionCycle.CHAOS] = ["无明确周期特征，市场处于无序状态"]

        # 选取得分最高的周期
        best_cycle = max(cycle_scores, key=cycle_scores.get)  # type: ignore[arg-type]
        best_score = cycle_scores[best_cycle]

        # 置信度计算: 最高分与第二分的差距
        sorted_scores = sorted(cycle_scores.values(), reverse=True)
        if len(sorted_scores) >= 2 and sorted_scores[0] > 0:
            confidence = min(0.99, (sorted_scores[0] - sorted_scores[1]) / sorted_scores[0])
        else:
            confidence = 0.5

        # 获取周期配置
        config = CYCLE_CONFIG[best_cycle]

        diagnosis = EmotionDiagnosis(
            current_cycle=best_cycle,
            confidence=round(confidence * 100, 1),
            indicators=indicators,
            position_limit=config["position_limit"],
            adapted_mode=config["adapted_mode"],
            core_principle=config["core_principle"],
            next_day_prediction=self._predict_next_day(best_cycle, indicators),
            reasons=reasons_map[best_cycle],
        )

        logger.info(
            "情绪周期研判完成",
            cycle=best_cycle.value,
            confidence=f"{diagnosis.confidence}%",
            position_limit=f"{diagnosis.position_limit}%",
        )

        return diagnosis

    def get_cycle_adaptation(self, cycle: EmotionCycle) -> Dict:
        """获取指定周期的适配配置

        Args:
            cycle: 情绪周期

        Returns:
            Dict 包含仓位上限、适配模式、核心原则
        """
        return CYCLE_CONFIG.get(cycle, CYCLE_CONFIG[EmotionCycle.CHAOS])

    def analyze_emotion_trend(self, days: int = 5) -> EmotionTrend:
        """情绪趋势分析

        基于历史情绪数据，分析情绪变化趋势、动量和加速度，
        并预判周期转换概率。

        Args:
            days: 分析天数

        Returns:
            EmotionTrend 情绪趋势分析结果
        """
        if len(self._emotion_history) < 2:
            return EmotionTrend(
                trend_direction="数据不足",
                extreme_warning="历史数据不足，无法进行趋势分析",
            )

        # 获取最近N天的情绪得分
        recent = self._emotion_history[-days:]
        scores = [s for _, s, _ in recent]
        dates = [d for d, _, _ in recent]

        current_score = scores[-1] if scores else 0.0

        # 计算趋势方向
        if len(scores) >= 3:
            # 使用线性回归斜率判断趋势
            n = len(scores)
            x_mean = (n - 1) / 2
            y_mean = sum(scores) / n
            numerator = sum((i - x_mean) * (scores[i] - y_mean) for i in range(n))
            denominator = sum((i - x_mean) ** 2 for i in range(n))
            slope = numerator / denominator if denominator > 0 else 0

            if slope > 5:
                trend_direction = "上升"
            elif slope < -5:
                trend_direction = "下降"
            else:
                trend_direction = "震荡"
        else:
            trend_direction = "数据不足"

        # 计算动量（最近3天的变化率）
        if len(scores) >= 3:
            momentum = ((scores[-1] - scores[-3]) / max(abs(scores[-3]), 1)) * 100
            momentum = max(-100, min(100, momentum))
        else:
            momentum = 0.0

        # 计算加速度（动量的变化）
        if len(scores) >= 5:
            recent_momentum = ((scores[-1] - scores[-2]) / max(abs(scores[-2]), 1)) * 100
            prev_momentum = ((scores[-3] - scores[-4]) / max(abs(scores[-4]), 1)) * 100
            acceleration = recent_momentum - prev_momentum
            acceleration = max(-100, min(100, acceleration))
        else:
            acceleration = 0.0

        # 周期转换概率预测
        current_cycle = self._emotion_history[-1][2] if self._emotion_history else EmotionCycle.CHAOS
        cycle_transition_prob = self._predict_cycle_transition(current_cycle, scores, momentum)

        # 极端值预警
        extreme_warning = self._check_extreme_warning(scores, current_cycle)

        return EmotionTrend(
            current_score=round(current_score, 2),
            trend_direction=trend_direction,
            momentum=round(momentum, 2),
            acceleration=round(acceleration, 2),
            cycle_transition_prob=cycle_transition_prob,
            extreme_warning=extreme_warning,
            history_scores=[round(s, 2) for s in scores],
        )

    def update_emotion_history(
        self,
        trade_date: date,
        indicators: EmotionIndicators,
        cycle: EmotionCycle,
    ) -> None:
        """更新情绪历史记录

        Args:
            trade_date: 交易日
            indicators: 情绪指标
            cycle: 情绪周期
        """
        # 计算综合情绪得分
        score = self._calculate_composite_score(indicators)

        # 去重（同一天只保留最新）
        self._emotion_history = [
            (d, s, c) for d, s, c in self._emotion_history
            if d != trade_date
        ]
        self._emotion_history.append((trade_date, score, cycle))

        # 保持最多60天历史
        if len(self._emotion_history) > 60:
            self._emotion_history = self._emotion_history[-60:]

        logger.debug(
            f"情绪历史更新: {trade_date.isoformat()}, score={score:.1f}, cycle={cycle.value}"
        )

    def adjust_weights_dynamically(
        self,
        indicators: EmotionIndicators,
        market_snap: MarketSnapshot,
    ) -> Dict[str, float]:
        """动态调整因子权重

        根据市场状态动态调整各因子权重，提高研判准确性。
        例如：在极端行情下，提高连板和资金因子的权重。

        Args:
            indicators: 情绪指标
            market_snap: 市场快照

        Returns:
            Dict 调整后的权重
        """
        adjustments = self._weight_adjustments.copy()

        # 极端行情检测
        is_extreme = False

        # 跌停过多 -> 提高连板因子权重
        if market_snap.limit_down_count > 15:
            adjustments["board"] = 1.5
            is_extreme = True

        # 炸板率极高 -> 提高大盘因子权重
        if indicators.explode_rate > 50:
            adjustments["market"] = 1.3
            is_extreme = True

        # 量能异常 -> 提高资金因子权重
        if abs(indicators.volume_change) > 30:
            adjustments["fund"] = 1.4
            is_extreme = True

        # 题材强度极高 -> 提高题材因子权重
        if indicators.theme_strength > 80:
            adjustments["theme"] = 1.3

        # 归一化权重
        total = sum(adjustments.values())
        if total > 0:
            adjustments = {k: v / total * 4 for k, v in adjustments.items()}

        self._weight_adjustments = adjustments

        if is_extreme:
            logger.info("检测到极端行情，已动态调整因子权重", adjustments=adjustments)

        return adjustments

    def get_emotion_extreme_signals(self, indicators: EmotionIndicators) -> List[Dict]:
        """获取情绪极端信号

        检测市场情绪的极端状态，提供预警信号。

        Args:
            indicators: 情绪指标

        Returns:
            List[Dict] 极端信号列表
        """
        signals: List[Dict] = []

        # 冰点信号
        if indicators.up_down_ratio < 0.3 and indicators.profit_effect < 20:
            signals.append({
                "type": "冰点",
                "level": "critical",
                "description": f"涨跌比{indicators.up_down_ratio:.2f}，赚钱效应{indicators.profit_effect:.1f}%",
                "advice": "情绪极度悲观，可能接近底部，关注恐慌盘后的修复机会",
            })

        # 高潮信号
        if indicators.profit_effect > 80 and indicators.explode_rate < 15:
            signals.append({
                "type": "高潮",
                "level": "critical",
                "description": f"赚钱效应{indicators.profit_effect:.1f}%，炸板率{indicators.explode_rate:.1f}%",
                "advice": "情绪极度乐观，随时可能分化，注意兑现利润",
            })

        # 恐慌信号
        if indicators.explode_rate > 60 and indicators.break_rate > 50:
            signals.append({
                "type": "恐慌",
                "level": "high",
                "description": f"炸板率{indicators.explode_rate:.1f}%，断板率{indicators.break_rate:.1f}%",
                "advice": "市场恐慌情绪蔓延，避免接力操作",
            })

        # 量价背离信号
        if indicators.volume_change > 30 and indicators.profit_effect < 30:
            signals.append({
                "type": "量价背离",
                "level": "high",
                "description": f"量能放大{indicators.volume_change:.1f}%但赚钱效应仅{indicators.profit_effect:.1f}%",
                "advice": "放量不涨，警惕主力出货",
            })

        # 缩量阴跌信号
        if indicators.volume_change < -30 and indicators.up_down_ratio < 0.5:
            signals.append({
                "type": "缩量阴跌",
                "level": "medium",
                "description": f"量能萎缩{abs(indicators.volume_change):.1f}%，涨跌比{indicators.up_down_ratio:.2f}",
                "advice": "无量阴跌，等待放量企稳信号",
            })

        return signals

    # ==================== 情绪趋势辅助方法 ====================

    def _calculate_composite_score(self, indicators: EmotionIndicators) -> float:
        """计算综合情绪得分 (0-100)"""
        score = 0.0

        # 涨跌比得分 (0-25)
        if indicators.up_down_ratio > 2.0:
            score += 25
        elif indicators.up_down_ratio > 1.5:
            score += 20
        elif indicators.up_down_ratio > 1.0:
            score += 15
        elif indicators.up_down_ratio > 0.6:
            score += 10
        else:
            score += 5

        # 炸板率得分 (0-25，低炸板率=高分)
        if indicators.explode_rate < 15:
            score += 25
        elif indicators.explode_rate < 30:
            score += 20
        elif indicators.explode_rate < 50:
            score += 15
        else:
            score += 5

        # 赚钱效应得分 (0-25)
        if indicators.profit_effect > 60:
            score += 25
        elif indicators.profit_effect > 40:
            score += 20
        elif indicators.profit_effect > 20:
            score += 15
        else:
            score += 5

        # 连板高度得分 (0-25)
        if indicators.max_consecutive_boards >= 7:
            score += 25
        elif indicators.max_consecutive_boards >= 5:
            score += 20
        elif indicators.max_consecutive_boards >= 3:
            score += 15
        else:
            score += 10

        return score

    def _predict_cycle_transition(
        self,
        current_cycle: EmotionCycle,
        scores: List[float],
        momentum: float,
    ) -> Dict[str, float]:
        """预测周期转换概率"""
        # 周期转换顺序
        cycle_order = [
            EmotionCycle.CHAOS,
            EmotionCycle.START,
            EmotionCycle.FERMENT,
            EmotionCycle.PEAK,
            EmotionCycle.DIVERGE,
            EmotionCycle.RETREAT,
        ]

        current_idx = cycle_order.index(current_cycle) if current_cycle in cycle_order else 0
        probs: Dict[str, float] = {}

        # 基于动量预测
        if momentum > 20:
            # 上升动量，向下一周期转换概率高
            if current_idx < len(cycle_order) - 1:
                next_cycle = cycle_order[current_idx + 1]
                probs[next_cycle.value] = min(80, 50 + momentum * 0.5)
                probs[current_cycle.value] = 100 - probs[next_cycle.value]
            else:
                probs[current_cycle.value] = 70
                probs[cycle_order[0].value] = 30
        elif momentum < -20:
            # 下降动量，向前一周期转换概率高
            if current_idx > 0:
                prev_cycle = cycle_order[current_idx - 1]
                probs[prev_cycle.value] = min(80, 50 + abs(momentum) * 0.5)
                probs[current_cycle.value] = 100 - probs[prev_cycle.value]
            else:
                probs[current_cycle.value] = 70
                probs[cycle_order[-1].value] = 30
        else:
            # 动量不足，维持当前周期
            probs[current_cycle.value] = 70
            if current_idx < len(cycle_order) - 1:
                probs[cycle_order[current_idx + 1].value] = 15
            if current_idx > 0:
                probs[cycle_order[current_idx - 1].value] = 15

        return probs

    def _check_extreme_warning(
        self,
        scores: List[float],
        current_cycle: EmotionCycle,
    ) -> Optional[str]:
        """检查极端值预警"""
        if not scores:
            return None

        current = scores[-1]

        # 连续3天得分>85，预警高潮
        if len(scores) >= 3 and all(s > 85 for s in scores[-3:]):
            return "情绪连续3天处于极高水平，警惕高潮后分化"

        # 连续3天得分<20，预警冰点
        if len(scores) >= 3 and all(s < 20 for s in scores[-3:]):
            return "情绪连续3天处于极低水平，可能接近冰点底部"

        # 单日暴跌
        if len(scores) >= 2 and scores[-2] - current > 30:
            return "情绪单日暴跌超30分，注意恐慌风险"

        # 单日暴涨
        if len(scores) >= 2 and current - scores[-2] > 30:
            return "情绪单日暴涨超30分，注意追高风险"

        return None

    # ==================== 指标计算方法 ====================

    def _calc_up_down_ratio(self, snap: MarketSnapshot) -> float:
        """计算涨跌家数比"""
        if snap.down_count <= 0:
            return 10.0 if snap.up_count > 0 else 1.0
        return snap.up_count / snap.down_count

    def _calc_profit_effect(self, snap: MarketSnapshot) -> float:
        """计算赚钱效应 (%上涨个股占比)"""
        total = snap.total_stocks
        if total <= 0:
            return 0.0
        return (snap.up_count / total) * 100

    def _calc_board_indicators(
        self, limit_ups: List[LimitUpStock]
    ) -> Tuple[int, float, float]:
        """计算连板指标: (最高连板, 晋级率, 断板率)

        Args:
            limit_ups: 涨停股列表

        Returns:
            Tuple[int, float, float]: (最高连板数, 晋级率%, 断板率%)
        """
        if not limit_ups:
            return 0, 0.0, 0.0

        # 最高连板
        max_boards = max(st.consecutive_boards for st in limit_ups)

        # 统计连板晋级率（有连板的股中成功晋级的比例）
        board_stocks = [st for st in limit_ups if st.consecutive_boards >= 2]
        if board_stocks:
            promoted = sum(1 for st in board_stocks if st.consecutive_boards >= 3)
            promotion_rate = (promoted / len(board_stocks)) * 100
        else:
            promotion_rate = 0.0

        # 断板率估算: 基于炸板次数
        total_explode = sum(st.explode_count for st in limit_ups)
        if len(limit_ups) > 0:
            break_rate = min(100.0, (total_explode / len(limit_ups)) * 20)
        else:
            break_rate = 0.0

        return max_boards, round(promotion_rate, 1), round(break_rate, 1)

    def _calc_dragon_premium(self, limit_ups: List[LimitUpStock]) -> float:
        """计算龙头溢价 (%前日涨停股今日高开/上涨比例)"""
        if not limit_ups:
            return 0.0

        # 龙头定义: 最高连板的前5只
        leaders = sorted(limit_ups, key=lambda x: x.consecutive_boards, reverse=True)[:5]

        # 龙头溢价: 龙头封单金额 / 龙头数量 的相对值
        avg_seal = sum(st.seal_amount for st in leaders) / len(leaders) if leaders else 0
        # 归一化为0-100的溢价指标（1亿元封单=50分）
        premium = min(100.0, avg_seal / 1e8 * 50)
        return premium

    def _calc_main_inflow(self, snap: MarketSnapshot) -> float:
        """计算主力资金净流入占比

        基于两市总成交额变化进行估算
        """
        # 简化模型: 量能放大+上涨 = 主力净流入
        volume_factor = max(-1.0, min(1.0, snap.volume_change_pct / 50))

        # 结合涨跌家数比修正
        ud_ratio = self._calc_up_down_ratio(snap)
        ud_factor = max(-1.0, min(1.0, (ud_ratio - 1.0)))

        # 综合计算净流入占比 (-100 ~ 100)
        inflow_ratio = (volume_factor + ud_factor) * 50
        return inflow_ratio

    def _calc_yingyou_activity(self, dragon_bonds: List[DragonBond]) -> float:
        """计算游资活跃度 (基于龙虎榜数据)"""
        if not dragon_bonds:
            return 0.0

        # 游资席位总买入金额
        yingyou_buys = sum(
            db.buy_amount for db in dragon_bonds if db.seat_type == "游资"
        )
        yingyou_sells = sum(
            db.sell_amount for db in dragon_bonds if db.seat_type == "游资"
        )

        # 活跃度 = 买卖合计 / 标准化系数
        total_activity = yingyou_buys + yingyou_sells
        # 归一化: 1亿=50分
        activity_score = min(100.0, total_activity / 1e8 * 50)

        # 净买入加分
        net_ratio = (yingyou_buys - yingyou_sells) / (yingyou_buys + yingyou_sells + 1)
        activity_score += net_ratio * 20

        return min(100.0, activity_score)

    def _calc_northbound_flow(self, snap: MarketSnapshot) -> float:
        """计算北向资金流向指标

        基于市场量价特征进行估算
        """
        # 简化模型: 结合指数表现和量能变化
        # 实际应使用真实北向资金数据
        sh_change = snap.sh_index * 0.01  # 使用上证指数变化作为代理
        volume_change = snap.volume_change_pct

        # 综合估算
        flow = sh_change * 30 + volume_change * 0.5
        return max(-100.0, min(100.0, flow))

    def _calc_theme_strength(self, themes: List[ThemeData]) -> float:
        """计算主线板块强度

        基于涨停家数最多题材的表现
        """
        if not themes:
            return 0.0

        # 找到最强题材
        strongest = max(themes, key=lambda t: t.limit_up_count + len(t.stocks) * 0.1)

        # 强度 = 涨停数 * 10 + 成分股平均涨幅
        strength = strongest.limit_up_count * 10 + strongest.avg_change_pct
        return min(100.0, strength)

    def _calc_sector_linkage(self, themes: List[ThemeData]) -> float:
        """计算板块联动性

        统计多个题材同时活跃的程度
        """
        if len(themes) < 2:
            return 0.0

        # 活跃题材定义: 有涨停股或平均涨幅>2%
        active_themes = [
            t for t in themes if t.limit_up_count > 0 or t.avg_change_pct > 2.0
        ]

        # 联动性 = 活跃题材数 / 总题材数
        if len(themes) > 0:
            linkage = (len(active_themes) / len(themes)) * 100
        else:
            linkage = 0.0

        return linkage

    def _calc_theme_sustainability(self, themes: List[ThemeData]) -> float:
        """计算题材持续性

        基于题材连续活跃天数的估算（当前使用mock）
        """
        if not themes:
            return 0.0

        # 持续性评估: 有龙头+多涨停+资金净流入 = 持续性好
        sustained_count = 0
        for t in themes:
            if t.leading_stock and t.limit_up_count >= 3 and t.total_inflow > 0:
                sustained_count += 1

        if len(themes) > 0:
            sustainability = (sustained_count / len(themes)) * 100
        else:
            sustainability = 0.0

        return sustainability

    # ==================== 周期判定方法 ====================

    def _score_retreat(self, indicators: EmotionIndicators) -> Tuple[float, List[str]]:
        """退潮期得分计算"""
        score = 0.0
        reasons: List[str] = []
        t = CYCLE_THRESHOLDS["retreat"]

        if indicators.up_down_ratio < t["up_down_ratio"]:
            score += 0.3
            reasons.append(f"涨跌家数比{indicators.up_down_ratio:.2f}<0.3，情绪极度悲观")

        limit_down = self._last_snapshot.limit_down_count if self._last_snapshot else 0
        if limit_down >= 15 or indicators.break_rate > t["break_rate"]:
            score += 0.25
            reasons.append(f"跌停{limit_down}只或断板率{indicators.break_rate:.1f}%高")

        if indicators.max_consecutive_boards <= t["max_consecutive_boards"]:
            score += 0.2
            reasons.append(f"最高连板仅{indicators.max_consecutive_boards}板，接力意愿弱")

        if indicators.explode_rate > t["explode_rate"]:
            score += 0.15
            reasons.append(f"炸板率{indicators.explode_rate:.1f}%极高")

        if indicators.profit_effect < 30:
            score += 0.1
            reasons.append(f"赚钱效应{indicators.profit_effect:.1f}%，亏钱面大")

        return score, reasons

    def _score_peak(self, indicators: EmotionIndicators) -> Tuple[float, List[str]]:
        """高潮期得分计算"""
        score = 0.0
        reasons: List[str] = []
        t = CYCLE_THRESHOLDS["peak"]

        limit_up = self._last_snapshot.limit_up_count if self._last_snapshot else 0
        if limit_up >= t["limit_up_count"]:
            score += 0.3
            reasons.append(f"涨停{limit_up}只，情绪全面高潮")

        if indicators.profit_effect >= t["profit_effect"]:
            score += 0.25
            reasons.append(f"赚钱效应{indicators.profit_effect:.1f}%，普涨格局")

        if indicators.up_down_ratio >= t["up_down_ratio"]:
            score += 0.2
            reasons.append(f"涨跌家数比{indicators.up_down_ratio:.2f}，情绪极热")

        if indicators.explode_rate <= t["explode_rate"] and limit_up > 50:
            score += 0.15
            reasons.append(f"炸板率{indicators.explode_rate:.1f}%低，封板质量好")

        if indicators.max_consecutive_boards >= t["max_consecutive_boards"]:
            score += 0.1
            reasons.append(f"最高连板{indicators.max_consecutive_boards}板，高度打开")

        return score, reasons

    def _score_diverge(self, indicators: EmotionIndicators) -> Tuple[float, List[str]]:
        """分歧期得分计算"""
        score = 0.0
        reasons: List[str] = []
        t = CYCLE_THRESHOLDS["diverge"]

        if indicators.explode_rate > t["explode_rate"]:
            score += 0.3
            reasons.append(f"炸板率{indicators.explode_rate:.1f}%升高，分歧加大")

        limit_down = self._last_snapshot.limit_down_count if self._last_snapshot else 0
        if limit_down >= t["limit_down_count"]:
            score += 0.2
            reasons.append(f"跌停{limit_down}只，亏钱效应扩散")

        if indicators.break_rate > t["break_rate"]:
            score += 0.2
            reasons.append(f"断板率{indicators.break_rate:.1f}%升高，连板接力困难")

        if 0.8 <= indicators.up_down_ratio <= 1.5:
            score += 0.15
            reasons.append(f"涨跌家数比{indicators.up_down_ratio:.2f}，涨跌互现")

        if indicators.profit_effect < 50:
            score += 0.15
            reasons.append(f"赚钱效应{indicators.profit_effect:.1f}%回落")

        return score, reasons

    def _score_ferment(self, indicators: EmotionIndicators) -> Tuple[float, List[str]]:
        """发酵期得分计算"""
        score = 0.0
        reasons: List[str] = []
        t = CYCLE_THRESHOLDS["ferment"]

        limit_up = self._last_snapshot.limit_up_count if self._last_snapshot else 0
        if limit_up >= t["limit_up_count"]:
            score += 0.3
            reasons.append(f"涨停{limit_up}只，主线发酵")

        if indicators.up_down_ratio >= t["up_down_ratio"]:
            score += 0.2
            reasons.append(f"涨跌家数比{indicators.up_down_ratio:.2f}，情绪向好")

        if indicators.promotion_rate >= t["promotion_rate"]:
            score += 0.2
            reasons.append(f"晋级率{indicators.promotion_rate:.1f}%，接力良好")

        if indicators.max_consecutive_boards >= t["max_consecutive_boards"]:
            score += 0.15
            reasons.append(f"最高连板{indicators.max_consecutive_boards}板，高度持续")

        if indicators.theme_strength >= 50:
            score += 0.15
            reasons.append(f"主线强度{indicators.theme_strength:.1f}，板块效应好")

        return score, reasons

    def _score_start(self, indicators: EmotionIndicators) -> Tuple[float, List[str]]:
        """启动期得分计算"""
        score = 0.0
        reasons: List[str] = []
        t = CYCLE_THRESHOLDS["start"]

        if indicators.up_down_ratio >= t["up_down_ratio"]:
            score += 0.3
            reasons.append(f"涨跌家数比{indicators.up_down_ratio:.2f}>1.2，情绪回暖")

        limit_up = self._last_snapshot.limit_up_count if self._last_snapshot else 0
        if limit_up >= t["limit_up_count"]:
            score += 0.25
            reasons.append(f"涨停{limit_up}只，活跃资金入场")

        if indicators.max_consecutive_boards >= t["max_consecutive_boards"]:
            score += 0.2
            reasons.append(f"最高连板{indicators.max_consecutive_boards}板，高度突破")

        if indicators.volume_change >= t["volume_change"]:
            score += 0.15
            reasons.append(f"量能放大{indicators.volume_change:.1f}%，资金回流")

        if indicators.dragon_premium > 30:
            score += 0.1
            reasons.append(f"龙头溢价{indicators.dragon_premium:.1f}，试错资金积极")

        return score, reasons

    def _predict_next_day(self, current_cycle: EmotionCycle, indicators: EmotionIndicators) -> str:
        """基于当前周期预判次日走势"""
        predictions = {
            EmotionCycle.CHAOS: "市场仍处于混沌期，次日大概率继续震荡整理，等待新题材破冰。",
            EmotionCycle.START: "情绪启动中，次日若量能配合有望继续发酵，关注新主线持续性。",
            EmotionCycle.FERMENT: "主线发酵良好，次日大概率延续强势，关注龙头封单和后排跟风。",
            EmotionCycle.PEAK: "情绪达到高潮，次日大概率分化分歧，注意兑现利润防范风险。",
            EmotionCycle.DIVERGE: "分歧加大中，次日若不能快速修复可能进入退潮，需谨慎应对。",
            EmotionCycle.RETREAT: "情绪退潮中，次日大概率继续弱势，防守为主等待情绪企稳。",
        }

        base_prediction = predictions.get(current_cycle, "市场状态不明，保持观察。")

        # 结合量能变化修正
        if indicators.volume_change > 20:
            base_prediction += " 注意量能异常放大，可能加速周期转换。"
        elif indicators.volume_change < -20:
            base_prediction += " 量能萎缩，观望情绪浓厚。"

        return base_prediction
