"""分战法智能筛选引擎 — 4步研判体系

核心筛选流程:
  Step 1: 硬性条件筛选 — 检查战法5项硬性条件是否全部满足
  Step 2: 形态识别 — 评估3项加分形态条件，计算形态得分
  Step 3: 环境适配 — 判断当前市场环境是否适合该战法
  Step 4: 持续性判定 — 综合评分并预测持续性

输出: TacticMatchResult 包含匹配分数、研判结论、操作建议

Author: SWAT Engine
Version: 2.0.0
"""

import asyncio
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from ...core.config import AppConfig
from ...core.exceptions import ModuleError
from ...core.logger import get_logger
from ...data_platform.data_models import TacticMatchResult
from .tactics_library import (
    ALL_TACTICS,
    TACTICS_BY_CYCLE,
    TacticRuleSet,
    get_tactic_by_code,
    get_tactic_by_name,
)

logger = get_logger("swat.m05.screener")


# ──────────────────────────────────────────────────────────
# 常量定义
# ──────────────────────────────────────────────────────────

# 硬性条件权重分配（5项条件，每项基础权重0.2）
HARD_CONDITION_BASE_WEIGHT = 0.20

# 形态条件权重分配（3项条件，总权重0.3）
SHAPE_CONDITION_TOTAL_WEIGHT = 0.30

# 环境适配权重
ENV_ADAPT_WEIGHT = 0.25

# 持续性权重
SUSTAINABILITY_WEIGHT = 0.15

# 硬性条件满分阈值（必须全部满足）
HARD_CONDITION_PASS_THRESHOLD = 1.0  # 100%

# 综合评分阈值
SCORE_PASS_THRESHOLD = 65.0
SCORE_EXCELLENT_THRESHOLD = 80.0


# ═══════════════════════════════════════════════════════
# Step 1: 硬性条件筛选器
# ═══════════════════════════════════════════════════════

class HardConditionChecker:
    """硬性条件检查器 — Step 1

    逐项检查战法的5项硬性条件，每项条件必须满足才能通过。
    输出每项条件的检查结果（通过/失败）及总体通过率。
    """

    def __init__(self):
        self.check_methods = {
            "chip_concentration_low": self._check_chip_concentration,
            "chip_peak_shape": self._check_chip_peak_shape,
            "profit_ratio": self._check_profit_ratio,
            "breakout_today": self._check_breakout,
            "change_pct_today": self._check_change_pct,
            "volume_ma5_ratio": self._check_volume_ma5_ratio,
            "volume_ma20_ratio": self._check_volume_ma20_ratio,
            "price_breakout": self._check_price_breakout,
            "seal_quality": self._check_seal_quality,
            "volume_shrink_ratio": self._check_volume_shrink_ratio,
            "price_breakout_high": self._check_price_breakout_high,
            "chip_lock_ratio": self._check_chip_lock_ratio,
            "turnover_rate": self._check_turnover_rate,
            "break_left_peak": self._check_break_left_peak,
            "breakout_margin_pct": self._check_breakout_margin,
            "volume_vs_left_peak": self._check_volume_vs_left_peak,
            "upper_shadow_volume_ok": self._check_upper_shadow_volume,
            "is_leader_stock": self._check_is_leader,
            "consecutive_boards_before": self._check_consecutive_boards,
            "is_first_yin_after_rally": self._check_is_first_yin,
            "price_vs_ma5": self._check_price_vs_ma5,
            "first_wave_gain_pct": self._check_first_wave_gain,
            "washout_volume_ratio": self._check_washout_volume,
            "washout_support_hold": self._check_washout_support,
            "second_wave_volume_ratio": self._check_second_wave_volume,
            "second_wave_change_pct": self._check_second_wave_change,
            "consecutive_doji_count": self._check_consecutive_doji,
            "doji_volume_vs_ma20": self._check_doji_volume,
            "reversal_candle": self._check_reversal_candle,
            "reversal_volume_ratio": self._check_reversal_volume,
            "is_in_bottom_area": self._check_is_in_bottom,
            "platform_days": self._check_platform_days,
            "platform_amplitude_pct": self._check_platform_amplitude,
            "breakout_volume_ratio": self._check_breakout_volume,
            "breakout_body_pct": self._check_breakout_body,
            "is_first_board_yesterday": self._check_is_first_board,
            "first_board_seal_time": self._check_first_board_seal_time,
            "next_day_open_high_pct": self._check_next_day_open,
            "auction_volume_ratio": self._check_auction_volume,
            "theme_in_ferment": self._check_theme_in_ferment,
            "dragon_rank": self._check_dragon_rank,
            "sector_limit_up_count": self._check_sector_limit_up,
            "emotion_cycle_match": self._check_emotion_cycle_match,
            "consecutive_boards": self._check_consecutive_boards_current,
            "sector_ladder_complete": self._check_sector_ladder,
            "boll_band_width_pct": self._check_boll_width,
            "price_vs_boll_upper": self._check_price_vs_boll_upper,
            "boll_squeeze_days": self._check_boll_squeeze_days,
            "boll_mid_direction": self._check_boll_mid_direction,
            "price_vs_vwap_ratio": self._check_price_vs_vwap,
            "vwap_touch_count": self._check_vwap_touch,
            "intraday_trend": self._check_intraday_trend,
            "volume_ratio_intraday": self._check_volume_ratio_intraday,
            "bottom_touch_count": self._check_bottom_touch,
            "third_bottom_vs_second": self._check_third_bottom,
            "neckline_breakout": self._check_neckline_breakout,
            "bottom_spacing_days": self._check_bottom_spacing,
            "prev_day_change_pct": self._check_prev_day_change,
            "today_change_pct": self._check_today_change,
            "price_engulf_prev_high": self._check_price_engulf,
            "today_volume_vs_yesterday": self._check_today_volume_vs_yesterday,
            "is_popular_stock": self._check_is_popular,
            "tail_volume_vs_avg": self._check_tail_volume,
            "tail_price_stable": self._check_tail_price_stable,
            "intraday_decline_pct": self._check_intraday_decline,
            "not_limit_down": self._check_not_limit_down,
            "next_day_up_expectation": self._check_next_day_expectation,
        }

    def check(self, tactic: TacticRuleSet, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行硬性条件检查

        Args:
            tactic: 战法规则集
            stock_data: 个股数据字典

        Returns:
            检查结果字典，包含每项条件的检查详情和总体结果
        """
        results = []
        passed_count = 0
        total_weight = 0.0
        earned_weight = 0.0

        for condition in tactic.hard_conditions:
            indicator = condition["indicator"]
            method = self.check_methods.get(indicator, self._check_generic)
            passed = method(condition, stock_data)
            weight = condition.get("weight", HARD_CONDITION_BASE_WEIGHT)

            results.append({
                "name": condition["name"],
                "indicator": indicator,
                "threshold": condition["threshold"],
                "actual_value": stock_data.get(indicator),
                "passed": passed,
                "weight": weight,
            })

            total_weight += weight
            if passed:
                passed_count += 1
                earned_weight += weight

        pass_rate = earned_weight / total_weight if total_weight > 0 else 0.0

        return {
            "step": "硬性条件",
            "results": results,
            "passed_count": passed_count,
            "total_count": len(tactic.hard_conditions),
            "pass_rate": round(pass_rate, 4),
            "passed": pass_rate >= HARD_CONDITION_PASS_THRESHOLD,
            "score": round(pass_rate * 40, 1),  # 硬性条件占40分
        }

    # ── 具体检查方法 ────────────────────────────

    def _check_generic(self, condition: Dict, data: Dict) -> bool:
        """通用条件检查"""
        indicator = condition["indicator"]
        operator = condition["operator"]
        threshold = condition["threshold"]
        actual = data.get(indicator)

        if actual is None:
            return False

        return self._compare(actual, operator, threshold)

    def _compare(self, actual: Any, operator: str, threshold: Any) -> bool:
        """通用比较操作"""
        try:
            if operator == "ge":
                return float(actual) >= float(threshold)
            elif operator == "gt":
                return float(actual) > float(threshold)
            elif operator == "le":
                return float(actual) <= float(threshold)
            elif operator == "lt":
                return float(actual) < float(threshold)
            elif operator == "eq":
                return actual == threshold
            elif operator == "between":
                low, high = threshold
                return low <= float(actual) <= high
        except (ValueError, TypeError):
            return False
        return False

    def _check_chip_concentration(self, condition: Dict, data: Dict) -> bool:
        return data.get("chip_concentration_low", 0) >= condition["threshold"]

    def _check_chip_peak_shape(self, condition: Dict, data: Dict) -> bool:
        return data.get("chip_peak_shape", "") == condition["threshold"]

    def _check_profit_ratio(self, condition: Dict, data: Dict) -> bool:
        return data.get("profit_ratio", 0) >= condition["threshold"]

    def _check_breakout(self, condition: Dict, data: Dict) -> bool:
        return bool(data.get("breakout_today", False))

    def _check_change_pct(self, condition: Dict, data: Dict) -> bool:
        return data.get("change_pct_today", 0) >= condition["threshold"]

    def _check_volume_ma5_ratio(self, condition: Dict, data: Dict) -> bool:
        return data.get("volume_ma5_ratio", 0) >= condition["threshold"]

    def _check_volume_ma20_ratio(self, condition: Dict, data: Dict) -> bool:
        return data.get("volume_ma20_ratio", 0) >= condition["threshold"]

    def _check_price_breakout(self, condition: Dict, data: Dict) -> bool:
        return bool(data.get("price_breakout", False))

    def _check_seal_quality(self, condition: Dict, data: Dict) -> bool:
        return data.get("seal_quality", 0) >= condition["threshold"]

    def _check_volume_shrink_ratio(self, condition: Dict, data: Dict) -> bool:
        return data.get("volume_shrink_ratio", 100) <= condition["threshold"]

    def _check_price_breakout_high(self, condition: Dict, data: Dict) -> bool:
        return bool(data.get("price_breakout_high", False))

    def _check_chip_lock_ratio(self, condition: Dict, data: Dict) -> bool:
        return data.get("chip_lock_ratio", 0) >= condition["threshold"]

    def _check_turnover_rate(self, condition: Dict, data: Dict) -> bool:
        tr = data.get("turnover_rate", 999)
        th = condition["threshold"]
        if isinstance(th, tuple):
            return th[0] <= tr <= th[1]
        return tr <= th

    def _check_break_left_peak(self, condition: Dict, data: Dict) -> bool:
        return bool(data.get("break_left_peak", False))

    def _check_breakout_margin(self, condition: Dict, data: Dict) -> bool:
        return data.get("breakout_margin_pct", 0) >= condition["threshold"]

    def _check_volume_vs_left_peak(self, condition: Dict, data: Dict) -> bool:
        return data.get("volume_vs_left_peak", 0) >= condition["threshold"]

    def _check_upper_shadow_volume(self, condition: Dict, data: Dict) -> bool:
        return bool(data.get("upper_shadow_volume_ok", False))

    def _check_is_leader(self, condition: Dict, data: Dict) -> bool:
        return bool(data.get("is_leader_stock", False))

    def _check_consecutive_boards(self, condition: Dict, data: Dict) -> bool:
        return data.get("consecutive_boards_before", 0) >= condition["threshold"]

    def _check_is_first_yin(self, condition: Dict, data: Dict) -> bool:
        return bool(data.get("is_first_yin_after_rally", False))

    def _check_price_vs_ma5(self, condition: Dict, data: Dict) -> bool:
        return data.get("price_vs_ma5_ratio", 0) >= condition["threshold"]

    def _check_first_wave_gain(self, condition: Dict, data: Dict) -> bool:
        return data.get("first_wave_gain_pct", 0) >= condition["threshold"]

    def _check_washout_volume(self, condition: Dict, data: Dict) -> bool:
        return data.get("washout_volume_ratio", 100) <= condition["threshold"]

    def _check_washout_support(self, condition: Dict, data: Dict) -> bool:
        return bool(data.get("washout_support_hold", False))

    def _check_second_wave_volume(self, condition: Dict, data: Dict) -> bool:
        return data.get("second_wave_volume_ratio", 0) >= condition["threshold"]

    def _check_second_wave_change(self, condition: Dict, data: Dict) -> bool:
        return data.get("second_wave_change_pct", 0) >= condition["threshold"]

    def _check_consecutive_doji(self, condition: Dict, data: Dict) -> bool:
        return data.get("consecutive_doji_count", 0) >= condition["threshold"]

    def _check_doji_volume(self, condition: Dict, data: Dict) -> bool:
        return data.get("doji_volume_vs_ma20", 100) <= condition["threshold"]

    def _check_reversal_candle(self, condition: Dict, data: Dict) -> bool:
        return bool(data.get("reversal_candle", False))

    def _check_reversal_volume(self, condition: Dict, data: Dict) -> bool:
        return data.get("reversal_volume_ratio", 0) >= condition["threshold"]

    def _check_is_in_bottom(self, condition: Dict, data: Dict) -> bool:
        return bool(data.get("is_in_bottom_area", False))

    def _check_platform_days(self, condition: Dict, data: Dict) -> bool:
        return data.get("platform_days", 0) >= condition["threshold"]

    def _check_platform_amplitude(self, condition: Dict, data: Dict) -> bool:
        return data.get("platform_amplitude_pct", 999) <= condition["threshold"]

    def _check_breakout_volume(self, condition: Dict, data: Dict) -> bool:
        return data.get("breakout_volume_ratio", 0) >= condition["threshold"]

    def _check_breakout_body(self, condition: Dict, data: Dict) -> bool:
        return data.get("breakout_body_pct", 0) >= condition["threshold"]

    def _check_is_first_board(self, condition: Dict, data: Dict) -> bool:
        return bool(data.get("is_first_board_yesterday", False))

    def _check_first_board_seal_time(self, condition: Dict, data: Dict) -> bool:
        return data.get("first_board_seal_time", 999) <= condition["threshold"]

    def _check_next_day_open(self, condition: Dict, data: Dict) -> bool:
        val = data.get("next_day_open_high_pct", -999)
        low, high = condition["threshold"]
        return low <= val <= high

    def _check_auction_volume(self, condition: Dict, data: Dict) -> bool:
        return data.get("auction_volume_ratio", 0) >= condition["threshold"]

    def _check_theme_in_ferment(self, condition: Dict, data: Dict) -> bool:
        return bool(data.get("theme_in_ferment", False))

    def _check_dragon_rank(self, condition: Dict, data: Dict) -> bool:
        return data.get("dragon_rank", 999) <= condition["threshold"]

    def _check_sector_limit_up(self, condition: Dict, data: Dict) -> bool:
        return data.get("sector_limit_up_count", 0) >= condition["threshold"]

    def _check_emotion_cycle_match(self, condition: Dict, data: Dict) -> bool:
        return bool(data.get("emotion_cycle_match", False))

    def _check_consecutive_boards_current(self, condition: Dict, data: Dict) -> bool:
        return data.get("consecutive_boards", 0) >= condition["threshold"]

    def _check_sector_ladder(self, condition: Dict, data: Dict) -> bool:
        return bool(data.get("sector_ladder_complete", False))

    def _check_boll_width(self, condition: Dict, data: Dict) -> bool:
        return data.get("boll_band_width_pct", 999) <= condition["threshold"]

    def _check_price_vs_boll_upper(self, condition: Dict, data: Dict) -> bool:
        return data.get("price_vs_boll_upper", 0) >= condition["threshold"]

    def _check_boll_squeeze_days(self, condition: Dict, data: Dict) -> bool:
        return data.get("boll_squeeze_days", 0) >= condition["threshold"]

    def _check_boll_mid_direction(self, condition: Dict, data: Dict) -> bool:
        return data.get("boll_mid_direction", "") == condition["threshold"]

    def _check_price_vs_vwap(self, condition: Dict, data: Dict) -> bool:
        return data.get("price_vs_vwap_ratio", 0) >= condition["threshold"]

    def _check_vwap_touch(self, condition: Dict, data: Dict) -> bool:
        return data.get("vwap_touch_count", 0) >= condition["threshold"]

    def _check_intraday_trend(self, condition: Dict, data: Dict) -> bool:
        return data.get("intraday_trend", "") == condition["threshold"]

    def _check_volume_ratio_intraday(self, condition: Dict, data: Dict) -> bool:
        return data.get("volume_ratio_intraday", 0) >= condition["threshold"]

    def _check_bottom_touch(self, condition: Dict, data: Dict) -> bool:
        return data.get("bottom_touch_count", 0) >= condition["threshold"]

    def _check_third_bottom(self, condition: Dict, data: Dict) -> bool:
        return data.get("third_bottom_vs_second", 0) >= condition["threshold"]

    def _check_neckline_breakout(self, condition: Dict, data: Dict) -> bool:
        return bool(data.get("neckline_breakout", False))

    def _check_bottom_spacing(self, condition: Dict, data: Dict) -> bool:
        return data.get("bottom_spacing_days", 0) >= condition["threshold"]

    def _check_prev_day_change(self, condition: Dict, data: Dict) -> bool:
        return data.get("prev_day_change_pct", 0) <= condition["threshold"]

    def _check_today_change(self, condition: Dict, data: Dict) -> bool:
        return data.get("today_change_pct", 0) >= condition["threshold"]

    def _check_price_engulf(self, condition: Dict, data: Dict) -> bool:
        return data.get("price_engulf_prev_high", 0) >= condition["threshold"]

    def _check_today_volume_vs_yesterday(self, condition: Dict, data: Dict) -> bool:
        return data.get("today_volume_vs_yesterday", 0) >= condition["threshold"]

    def _check_is_popular(self, condition: Dict, data: Dict) -> bool:
        return bool(data.get("is_popular_stock", False))

    def _check_tail_volume(self, condition: Dict, data: Dict) -> bool:
        return data.get("tail_volume_vs_avg", 100) <= condition["threshold"]

    def _check_tail_price_stable(self, condition: Dict, data: Dict) -> bool:
        return bool(data.get("tail_price_stable", False))

    def _check_intraday_decline(self, condition: Dict, data: Dict) -> bool:
        return data.get("intraday_decline_pct", 0) >= condition["threshold"]

    def _check_not_limit_down(self, condition: Dict, data: Dict) -> bool:
        return bool(data.get("not_limit_down", True))

    def _check_next_day_expectation(self, condition: Dict, data: Dict) -> bool:
        return bool(data.get("next_day_up_expectation", False))


# ═══════════════════════════════════════════════════════
# Step 2: 形态识别评分器
# ═══════════════════════════════════════════════════════

class ShapeScorer:
    """形态识别评分器 — Step 2

    评估3项加分形态条件，每项条件根据满足程度给出不同分数。
    形态总分最高30分，直接加入综合评分。
    """

    def score(self, tactic: TacticRuleSet, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行形态评分

        Args:
            tactic: 战法规则集
            stock_data: 个股数据字典

        Returns:
            形态评分结果字典
        """
        results = []
        total_score = 0.0
        max_possible = 0.0

        for condition in tactic.shape_conditions:
            indicator = condition["indicator"]
            weight = condition.get("weight", 0.1)
            threshold = condition["threshold"]
            actual = stock_data.get(indicator)
            operator = condition.get("operator", "ge")

            # 计算满足度 (0-1)
            satisfaction = self._calc_satisfaction(actual, operator, threshold)
            score = satisfaction * weight * 100

            results.append({
                "name": condition["name"],
                "indicator": indicator,
                "threshold": threshold,
                "actual_value": actual,
                "satisfaction": round(satisfaction, 4),
                "score": round(score, 1),
                "max_score": round(weight * 100, 1),
            })

            total_score += score
            max_possible += weight * 100

        # 归一化到30分制
        normalized_score = (total_score / max_possible * 30) if max_possible > 0 else 0.0

        return {
            "step": "形态识别",
            "results": results,
            "raw_score": round(total_score, 1),
            "max_possible": round(max_possible, 1),
            "normalized_score": round(normalized_score, 1),
            "score": round(normalized_score, 1),  # 形态占30分
        }

    def _calc_satisfaction(self, actual: Any, operator: str, threshold: Any) -> float:
        """计算满足度 (0.0 - 1.0)"""
        if actual is None:
            return 0.0

        try:
            if operator == "eq":
                return 1.0 if actual == threshold else 0.0
            elif operator == "between":
                low, high = threshold
                val = float(actual)
                if low <= val <= high:
                    # 越接近中间值越满意
                    mid = (low + high) / 2
                    dist = abs(val - mid) / (high - low) * 2
                    return max(0.0, 1.0 - dist * 0.3)
                return 0.0
            elif operator in ("ge", "gt"):
                val = float(actual)
                th = float(threshold)
                if val < th:
                    return 0.0
                # 超出阈值越多，满足度越高，但有上限
                ratio = val / th if th > 0 else 1.0
                return min(1.0, 0.7 + (ratio - 1.0) * 0.3)
            elif operator in ("le", "lt"):
                val = float(actual)
                th = float(threshold)
                if val > th:
                    return 0.0
                ratio = val / th if th > 0 else 1.0
                return min(1.0, 0.7 + (1.0 - ratio) * 0.3)
        except (ValueError, TypeError, ZeroDivisionError):
            pass

        # 布尔值处理
        if isinstance(actual, bool):
            return 1.0 if actual else 0.0

        return 0.0


# ═══════════════════════════════════════════════════════
# Step 3: 环境适配评估器
# ═══════════════════════════════════════════════════════

class EnvironmentAdapter:
    """环境适配评估器 — Step 3

    评估当前市场环境是否适合该战法:
    - 涨停家数是否匹配
    - 涨跌比是否匹配
    - 量能趋势是否匹配
    - 题材强度是否匹配
    - 情绪周期是否匹配
    """

    def evaluate(self, tactic: TacticRuleSet,
                 market_env: Dict[str, Any]) -> Dict[str, Any]:
        """执行环境适配评估

        Args:
            tactic: 战法规则集
            market_env: 市场环境数据

        Returns:
            环境适配评估结果
        """
        best_env = tactic.best_env
        scores = []
        total_score = 0.0

        # 1. 涨停家数评估 (5分)
        limit_up_score = self._score_limit_up(best_env, market_env)
        scores.append({"name": "涨停家数", "score": limit_up_score})
        total_score += limit_up_score

        # 2. 涨跌比评估 (5分)
        ud_ratio_score = self._score_up_down_ratio(best_env, market_env)
        scores.append({"name": "涨跌比", "score": ud_ratio_score})
        total_score += ud_ratio_score

        # 3. 量能趋势评估 (5分)
        volume_score = self._score_volume_trend(best_env, market_env)
        scores.append({"name": "量能趋势", "score": volume_score})
        total_score += volume_score

        # 4. 题材强度评估 (5分)
        theme_score = self._score_theme_strength(best_env, market_env)
        scores.append({"name": "题材强度", "score": theme_score})
        total_score += theme_score

        # 5. 情绪周期评估 (5分)
        cycle_score = self._score_emotion_cycle(tactic, market_env)
        scores.append({"name": "情绪周期", "score": cycle_score})
        total_score += cycle_score

        return {
            "step": "环境适配",
            "scores": scores,
            "total_score": round(total_score, 1),
            "score": round(total_score, 1),  # 环境占25分
            "adaptation_level": self._adaptation_level(total_score),
        }

    def _score_limit_up(self, best_env: Dict, market: Dict) -> float:
        min_lu = best_env.get("min_limit_up", 0)
        max_lu = best_env.get("max_limit_up", 999)
        actual = market.get("limit_up_count", 0)
        if min_lu <= actual <= max_lu:
            return 5.0
        elif actual < min_lu * 0.7:
            return 1.0
        elif actual < min_lu:
            return 3.0
        elif actual > max_lu * 1.5:
            return 1.0
        else:
            return 3.0

    def _score_up_down_ratio(self, best_env: Dict, market: Dict) -> float:
        min_ud = best_env.get("min_up_down_ratio", 0.0)
        max_ud = best_env.get("max_up_down_ratio", 999.0)
        actual = market.get("up_down_ratio", 1.0)
        if min_ud <= actual <= max_ud:
            return 5.0
        elif actual < min_ud * 0.6:
            return 1.0
        elif actual < min_ud:
            return 3.0
        elif actual > max_ud * 1.3:
            return 2.0
        else:
            return 4.0

    def _score_volume_trend(self, best_env: Dict, market: Dict) -> float:
        expected = best_env.get("volume_trend", "any")
        actual = market.get("volume_trend", "stable")
        if expected == "any":
            return 5.0
        if expected == actual:
            return 5.0
        elif expected == "increase" and actual == "stable":
            return 3.0
        elif expected == "stable" and actual == "increase":
            return 3.0
        else:
            return 1.5

    def _score_theme_strength(self, best_env: Dict, market: Dict) -> float:
        expected = best_env.get("theme_requirement", "any")
        actual = market.get("theme_strength", "moderate")
        mapping = {"weak": 1, "moderate": 2, "strong": 3, "any": 2}
        exp_level = mapping.get(expected, 2)
        act_level = mapping.get(actual, 2)
        diff = abs(exp_level - act_level)
        if diff == 0:
            return 5.0
        elif diff == 1:
            return 3.0
        else:
            return 1.0

    def _score_emotion_cycle(self, tactic: TacticRuleSet, market: Dict) -> float:
        current_cycle = market.get("current_emotion_cycle", "混沌期")
        if current_cycle in tactic.applicable_cycles:
            return 5.0
        elif current_cycle in tactic.forbidden_cycles:
            return 0.0
        else:
            return 2.5

    def _adaptation_level(self, total_score: float) -> str:
        if total_score >= 22:
            return "高度适配"
        elif total_score >= 18:
            return "良好适配"
        elif total_score >= 12:
            return "基本适配"
        elif total_score >= 8:
            return "勉强适配"
        else:
            return "环境不适配"


# ═══════════════════════════════════════════════════════
# Step 4: 持续性判定器
# ═══════════════════════════════════════════════════════

class SustainabilityEvaluator:
    """持续性判定器 — Step 4

    综合前3步结果，判定战法匹配的持续性:
    - 硬性条件满分 → 持续性+5分
    - 形态得分高 → 持续性+3分
    - 环境适配好 → 持续性+4分
    - 额外加分项（游资介入、题材催化等）→ 最多+3分
    """

    def evaluate(self, hard_result: Dict, shape_result: Dict,
                 env_result: Dict, stock_data: Dict) -> Dict[str, Any]:
        """执行持续性评估

        Args:
            hard_result: Step 1 硬性条件结果
            shape_result: Step 2 形态评分结果
            env_result: Step 3 环境适配结果
            stock_data: 个股数据

        Returns:
            持续性评估结果
        """
        score = 0.0
        factors = []

        # 1. 硬性条件影响 (最高5分)
        hard_pass_rate = hard_result.get("pass_rate", 0)
        if hard_pass_rate >= 1.0:
            score += 5.0
            factors.append("硬性条件全部满足（+5分）")
        elif hard_pass_rate >= 0.8:
            score += 3.0
            factors.append("硬性条件大部分满足（+3分）")
        elif hard_pass_rate >= 0.6:
            score += 1.0
            factors.append("硬性条件部分满足（+1分）")

        # 2. 形态得分影响 (最高3分)
        shape_score = shape_result.get("score", 0)
        if shape_score >= 24:
            score += 3.0
            factors.append("形态得分优秀（+3分）")
        elif shape_score >= 18:
            score += 2.0
            factors.append("形态得分良好（+2分）")
        elif shape_score >= 12:
            score += 1.0
            factors.append("形态得分一般（+1分）")

        # 3. 环境适配影响 (最高4分)
        env_score = env_result.get("total_score", 0)
        if env_score >= 22:
            score += 4.0
            factors.append("环境高度适配（+4分）")
        elif env_score >= 18:
            score += 3.0
            factors.append("环境良好适配（+3分）")
        elif env_score >= 12:
            score += 1.5
            factors.append("环境基本适配（+1.5分）")

        # 4. 额外加分项 (最高3分)
        bonus = self._calc_bonus(stock_data)
        score += bonus["score"]
        factors.extend(bonus["reasons"])

        # 归一化到15分制
        final_score = min(15.0, score)

        return {
            "step": "持续性判定",
            "factors": factors,
            "raw_score": round(score, 1),
            "score": round(final_score, 1),  # 持续性占15分
            "sustainability_level": self._level(final_score),
            "prediction": self._prediction(final_score, stock_data),
        }

    def _calc_bonus(self, stock_data: Dict) -> Dict[str, Any]:
        """计算额外加分项"""
        bonus_score = 0.0
        reasons = []

        if stock_data.get("yingyou_intervention", False):
            bonus_score += 1.0
            reasons.append("知名游资介入（+1分）")

        if stock_data.get("theme_catalyst_active", False):
            bonus_score += 1.0
            reasons.append("题材催化持续（+1分）")

        if stock_data.get("fund_inflow_strong", False):
            bonus_score += 0.5
            reasons.append("主力资金持续流入（+0.5分）")

        if stock_data.get("technical_alignment", False):
            bonus_score += 0.5
            reasons.append("多技术指标共振（+0.5分）")

        return {"score": min(3.0, bonus_score), "reasons": reasons}

    def _level(self, score: float) -> str:
        if score >= 13:
            return "强持续"
        elif score >= 10:
            return "中等持续"
        elif score >= 7:
            return "弱持续"
        else:
            return "持续性差"

    def _prediction(self, score: float, stock_data: Dict) -> str:
        hold_period = stock_data.get("expected_hold_days", 3)
        if score >= 13:
            return f"持续性强劲，预期可持有{hold_period}天以上"
        elif score >= 10:
            return f"持续性良好，预期持有{hold_period}天左右"
        elif score >= 7:
            return f"持续性一般，建议持有不超过{hold_period}天"
        else:
            return "持续性差，建议隔日超短或放弃操作"


# ═══════════════════════════════════════════════════════
# 综合筛选引擎
# ═══════════════════════════════════════════════════════

class TacticScreener:
    """战法智能筛选引擎

    4步研判体系:
      Step 1: 硬性条件筛选 → 40分
      Step 2: 形态识别 → 30分
      Step 3: 环境适配 → 25分
      Step 4: 持续性判定 → 15分

    总分110分，65分以上入选，80分以上为优秀标的。
    """

    def __init__(self, config: Optional[AppConfig] = None):
        """初始化筛选引擎

        Args:
            config: 应用配置
        """
        self.config = config or AppConfig()
        self.hard_checker = HardConditionChecker()
        self.shape_scorer = ShapeScorer()
        self.env_adapter = EnvironmentAdapter()
        self.sustainability_eval = SustainabilityEvaluator()

        logger.info("战法智能筛选引擎初始化完成")

    async def screen_single(self, tactic: TacticRuleSet,
                           stock_data: Dict[str, Any],
                           market_env: Dict[str, Any]) -> Optional[TacticMatchResult]:
        """对单只个股执行单战法筛选

        Args:
            tactic: 战法规则集
            stock_data: 个股数据字典
            market_env: 市场环境数据

        Returns:
            TacticMatchResult 或 None（未通过筛选）
        """
        ticker = stock_data.get("ticker", "unknown")
        name = stock_data.get("name", "")

        logger.debug(f"开始筛选: {ticker} ({name}) vs {tactic.name}")

        # Step 1: 硬性条件
        hard_result = self.hard_checker.check(tactic, stock_data)
        if not hard_result["passed"]:
            logger.debug(f"{ticker} 未通过硬性条件: {hard_result['pass_rate']:.1%}")
            return None

        # Step 2: 形态识别
        shape_result = self.shape_scorer.score(tactic, stock_data)

        # Step 3: 环境适配
        env_result = self.env_adapter.evaluate(tactic, market_env)

        # Step 4: 持续性判定
        sustain_result = self.sustainability_eval.evaluate(
            hard_result, shape_result, env_result, stock_data
        )

        # 综合评分
        total_score = (
            hard_result["score"] +
            shape_result["score"] +
            env_result["score"] +
            sustain_result["score"]
        )

        # 生成研判结论
        shape_verdict = self._gen_shape_verdict(shape_result)
        adaptability = env_result["adaptation_level"]
        sustainability = sustain_result["sustainability_level"]
        prediction = sustain_result["prediction"]
        operation_guide = self._gen_operation_guide(total_score, tactic, stock_data)

        result = TacticMatchResult(
            tactic_name=tactic.name,
            ticker=ticker,
            stock_name=name,
            conditions_met=[r["name"] for r in hard_result["results"] if r["passed"]],
            conditions_failed=[r["name"] for r in hard_result["results"] if not r["passed"]],
            shape_verdict=shape_verdict,
            adaptability=adaptability,
            sustainability=sustainability,
            prediction=prediction,
            operation_guide=operation_guide,
            match_score=round(total_score, 1),
        )

        logger.info(
            f"筛选完成: {ticker} vs {tactic.name} | 总分={total_score:.1f} | "
            f"硬性={hard_result['score']:.1f} 形态={shape_result['score']:.1f} "
            f"环境={env_result['score']:.1f} 持续={sustain_result['score']:.1f}"
        )

        return result

    async def screen_batch(self, tactic: TacticRuleSet,
                          stock_list: List[Dict[str, Any]],
                          market_env: Dict[str, Any]) -> List[TacticMatchResult]:
        """批量筛选多只股

        Args:
            tactic: 战法规则集
            stock_list: 个股数据列表
            market_env: 市场环境数据

        Returns:
            通过筛选的战法匹配结果列表（按分数降序）
        """
        logger.info(f"批量筛选: 战法={tactic.name}, 标的数={len(stock_list)}")

        tasks = [
            self.screen_single(tactic, stock, market_env)
            for stock in stock_list
        ]
        results = await asyncio.gather(*tasks)

        # 过滤未通过和低于阈值的
        passed = [
            r for r in results
            if r is not None and r.match_score >= SCORE_PASS_THRESHOLD
        ]

        # 按分数降序排列
        passed.sort(key=lambda x: x.match_score, reverse=True)

        logger.info(f"批量筛选完成: {len(passed)}/{len(stock_list)} 只通过")
        return passed

    async def screen_all_tactics(self, stock_list: List[Dict[str, Any]],
                                  market_env: Dict[str, Any],
                                  tactic_codes: Optional[List[str]] = None
                                  ) -> Dict[str, List[TacticMatchResult]]:
        """对所有战法执行批量筛选

        Args:
            stock_list: 个股数据列表
            market_env: 市场环境数据
            tactic_codes: 指定战法编码列表，None则全部战法

        Returns:
            按战法名称分组的结果字典
        """
        tactics = ALL_TACTICS
        if tactic_codes:
            tactics = [t for t in tactics if t.code in tactic_codes]

        logger.info(f"全战法筛选: 战法数={len(tactics)}, 标的数={len(stock_list)}")

        results: Dict[str, List[TacticMatchResult]] = {}
        for tactic in tactics:
            tactic_results = await self.screen_batch(tactic, stock_list, market_env)
            if tactic_results:
                results[tactic.name] = tactic_results

        return results

    async def screen_by_emotion_cycle(self,
                                       stock_list: List[Dict[str, Any]],
                                       market_env: Dict[str, Any],
                                       cycle: str) -> Dict[str, List[TacticMatchResult]]:
        """根据情绪周期筛选适用战法

        Args:
            stock_list: 个股数据列表
            market_env: 市场环境数据
            cycle: 情绪周期名称

        Returns:
            按战法名称分组的结果字典
        """
        from .tactics_library import TACTICS_BY_CYCLE

        tactics = TACTICS_BY_CYCLE.get(cycle, [])
        if not tactics:
            logger.warning(f"周期 '{cycle}' 无适用战法")
            return {}

        logger.info(f"按周期筛选: 周期={cycle}, 适用战法={len(tactics)}")

        results: Dict[str, List[TacticMatchResult]] = {}
        for tactic in tactics:
            tactic_results = await self.screen_batch(tactic, stock_list, market_env)
            if tactic_results:
                results[tactic.name] = tactic_results

        return results

    def _gen_shape_verdict(self, shape_result: Dict) -> str:
        """生成形态研判结论"""
        score = shape_result["score"]
        if score >= 24:
            return "形态优秀，加分条件充分满足"
        elif score >= 18:
            return "形态良好，大部分加分条件满足"
        elif score >= 12:
            return "形态一般，部分加分条件满足"
        else:
            return "形态较差，加分条件不足"

    def _gen_operation_guide(self, total_score: float,
                             tactic: TacticRuleSet,
                             stock_data: Dict) -> str:
        """生成操作建议"""
        risk_boundary = tactic.risk_boundary
        stop_loss = risk_boundary.get("stop_loss_pct", -5.0)
        max_position = risk_boundary.get("max_position_pct", 30.0)
        max_hold = risk_boundary.get("max_hold_days", 5)

        if total_score >= 85:
            return (
                f"强烈推荐: 可配置{max_position:.0f}%仓位，"
                f"止损线{stop_loss:.0f}%，持有不超过{max_hold}天"
            )
        elif total_score >= 70:
            return (
                f"推荐参与: 配置{max_position * 0.7:.0f}%仓位，"
                f"止损线{stop_loss:.0f}%，持有不超过{max_hold}天"
            )
        elif total_score >= 65:
            return (
                f"可轻仓试错: 配置{max_position * 0.5:.0f}%仓位，"
                f"止损线{stop_loss * 0.8:.0f}%，持有不超过{max_hold - 1}天"
            )
        else:
            return "建议观望: 综合评分不足，不参与或极小仓位试探"


# ═══════════════════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════════════════

async def quick_screen(tactic_code: str,
                       stock_data: Dict[str, Any],
                       market_env: Dict[str, Any]) -> Optional[TacticMatchResult]:
    """快速单战法筛选（便捷函数）

    Args:
        tactic_code: 战法编码
        stock_data: 个股数据
        market_env: 市场环境

    Returns:
        TacticMatchResult 或 None
    """
    tactic = get_tactic_by_code(tactic_code)
    if tactic is None:
        return None

    screener = TacticScreener()
    return await screener.screen_single(tactic, stock_data, market_env)


async def multi_tactic_screen(stock_data: Dict[str, Any],
                               market_env: Dict[str, Any],
                               tactic_codes: Optional[List[str]] = None
                               ) -> List[TacticMatchResult]:
    """多战法同时筛选单只个股

    Args:
        stock_data: 个股数据
        market_env: 市场环境
        tactic_codes: 指定战法编码列表

    Returns:
        所有战法匹配结果列表（按分数降序）
    """
    tactics = ALL_TACTICS
    if tactic_codes:
        tactics = [t for t in tactics if t.code in tactic_codes]

    screener = TacticScreener()
    results = []

    for tactic in tactics:
        result = await screener.screen_single(tactic, stock_data, market_env)
        if result and result.match_score >= SCORE_PASS_THRESHOLD:
            results.append(result)

    results.sort(key=lambda x: x.match_score, reverse=True)
    return results
